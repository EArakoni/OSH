"""
Summarization service that coordinates between database and Gemini API
"""

import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from src.llm.gemini_client import GeminiClient
from src.database.db import Database

class LKMLSummarizer:
    """High-level service for generating LKML summaries"""
    
    def __init__(self, db: Database, gemini_client: GeminiClient):
        """
        Initialize summarizer
        
        Args:
            db: Database instance
            gemini_client: GeminiClient instance
        """
        self.db = db
        self.gemini = gemini_client
    
    def summarize_thread(self, thread_id: int, force: bool = False) -> Optional[Dict]:
        """
        Summarize a thread and store in database
        
        Args:
            thread_id: Database thread ID
            force: Regenerate even if summary exists
            
        Returns:
            Summary dictionary or None if error
        """
        # Check if summary already exists
        if not force:
            existing = self._get_existing_summary(thread_id, 'thread')
            if existing:
                print(f"✓ Thread {thread_id} already summarized")
                return existing
        
        # Get thread data
        cursor = self.db.conn.cursor()
        
        # Get thread metadata
        cursor.execute("SELECT * FROM threads WHERE id = ?", (thread_id,))
        thread_row = cursor.fetchone()
        if not thread_row:
            print(f"❌ Thread {thread_id} not found")
            return None
        
        thread_meta = dict(thread_row)
        
        # Get all emails in thread
        cursor.execute("""
            SELECT e.* 
            FROM emails e
            JOIN thread_emails te ON e.id = te.email_id
            WHERE te.thread_id = ?
            ORDER BY e.date ASC
        """, (thread_id,))
        
        thread_emails = [dict(row) for row in cursor.fetchall()]
        
        if not thread_emails:
            print(f"❌ No emails found for thread {thread_id}")
            return None
        
        print(f"📝 Summarizing thread: {thread_meta['subject']}")
        print(f"   Emails: {len(thread_emails)}, Participants: {thread_meta['participant_count']}")
        
        # Generate summary
        summary_data = self.gemini.summarize_thread(thread_emails, thread_meta)
        
        # Store in database
        self._store_summary(thread_id, 'thread', summary_data)
        
        print(f"✅ Thread summary generated")
        return summary_data
    
    def summarize_all_threads(self, limit: Optional[int] = None, 
                             min_emails: int = 2) -> int:
        """
        Summarize all threads in database
        
        Args:
            limit: Maximum number of threads to summarize
            min_emails: Only summarize threads with at least this many emails
            
        Returns:
            Number of threads summarized
        """
        cursor = self.db.conn.cursor()
        
        # Get threads that need summarization
        query = """
            SELECT t.id, t.subject, t.email_count
            FROM threads t
            LEFT JOIN summaries s ON s.thread_id = t.id AND s.summary_type = 'thread'
            WHERE s.id IS NULL AND t.email_count >= ?
            ORDER BY t.last_post DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (min_emails,))
        threads = cursor.fetchall()
        
        print(f"\n{'='*60}")
        print(f"Summarizing {len(threads)} threads")
        print(f"{'='*60}\n")
        
        success_count = 0
        total_cost = 0.0
        
        for idx, thread_row in enumerate(threads, 1):
            thread_id = thread_row['id']
            
            print(f"\n[{idx}/{len(threads)}] Thread {thread_id}: {thread_row['subject'][:60]}...")
            
            try:
                summary = self.summarize_thread(thread_id)
                if summary and not summary.get('error'):
                    success_count += 1
                    
                    # Estimate cost (rough)
                    cost = self.gemini.estimate_cost(
                        thread_row['email_count'] * 1000,  # Rough chars estimate
                        1000
                    )
                    total_cost += cost
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print(f"\n{'='*60}")
        print(f"✅ Summarized {success_count}/{len(threads)} threads")
        print(f"💰 Estimated cost: ${total_cost:.4f}")
        print(f"{'='*60}\n")
        
        return success_count
    
    def generate_daily_digest(self, date: str, force: bool = False) -> Optional[Dict]:
        """
        Generate daily digest for a specific date
        
        Args:
            date: Date string (YYYY-MM-DD)
            force: Regenerate even if exists
            
        Returns:
            Digest dictionary or None if error
        """
        # Check if digest already exists
        if not force:
            existing = self._get_existing_digest(date)
            if existing:
                print(f"✓ Digest for {date} already exists")
                return existing
        
        # Get all threads from that day
        cursor = self.db.conn.cursor()
        
        # Parse date
        try:
            date_obj = datetime.fromisoformat(date)
            next_day = date_obj + timedelta(days=1)
        except ValueError:
            print(f"❌ Invalid date format: {date}")
            return None
        
        # Get threads with summaries from that day
        cursor.execute("""
            SELECT t.*, s.tldr, s.key_points, s.important_changes, s.mentioned_subsystems
            FROM threads t
            LEFT JOIN summaries s ON s.thread_id = t.id AND s.summary_type = 'thread'
            WHERE t.first_post >= ? AND t.first_post < ?
            ORDER BY t.email_count DESC, t.last_post DESC
        """, (date, next_day.isoformat()))
        
        threads = [dict(row) for row in cursor.fetchall()]
        
        if not threads:
            print(f"❌ No threads found for {date}")
            return None
        
        print(f"📅 Generating digest for {date}")
        print(f"   Threads: {len(threads)}")
        
        # Ensure threads have summaries
        unsummarized = [t for t in threads if not t.get('tldr')]
        if unsummarized:
            print(f"   Summarizing {len(unsummarized)} threads first...")
            for thread in unsummarized:
                self.summarize_thread(thread['id'])
            
            # Re-fetch with summaries
            cursor.execute("""
                SELECT t.*, s.tldr, s.key_points, s.important_changes, s.mentioned_subsystems
                FROM threads t
                LEFT JOIN summaries s ON s.thread_id = t.id AND s.summary_type = 'thread'
                WHERE t.first_post >= ? AND t.first_post < ?
                ORDER BY t.email_count DESC, t.last_post DESC
            """, (date, next_day.isoformat()))
            
            threads = [dict(row) for row in cursor.fetchall()]
        
        # Prepare thread data for digest
        threads_data = []
        for thread in threads:
            threads_data.append({
                'subject': thread['subject'],
                'tldr': thread.get('tldr', 'No summary'),
                'subsystems': json.loads(thread.get('mentioned_subsystems', '[]')) if thread.get('mentioned_subsystems') else [],
                'importance': 'medium',  # Could enhance this
                'email_count': thread['email_count']
            })
        
        # Generate digest
        digest_data = self.gemini.generate_daily_digest(threads_data, date)
        
        # Store digest
        self._store_digest(date, digest_data)
        
        print(f"✅ Daily digest generated")
        return digest_data
    
    def _get_existing_summary(self, thread_id: int, 
                             summary_type: str) -> Optional[Dict]:
        """Check if summary already exists"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM summaries 
            WHERE thread_id = ? AND summary_type = ?
            ORDER BY generated_at DESC
            LIMIT 1
        """, (thread_id, summary_type))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def _get_existing_digest(self, date: str) -> Optional[Dict]:
        """Check if daily digest already exists"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM summaries 
            WHERE summary_type = 'daily' AND summary_date = ?
            ORDER BY generated_at DESC
            LIMIT 1
        """, (date,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def _store_summary(self, thread_id: int, summary_type: str, 
                      summary_data: Dict):
        """Store summary in database"""
        cursor = self.db.conn.cursor()
        
        # Convert lists/dicts to JSON
        key_points_json = json.dumps(summary_data.get('key_points', []))
        
        important_changes = {
            'resolution': summary_data.get('resolution', ''),
            'action_items': summary_data.get('action_items', []),
            'discussion_summary': summary_data.get('discussion_summary', '')
        }
        important_changes_json = json.dumps(important_changes)
        
        subsystems_json = json.dumps(summary_data.get('subsystems', []))
        
        cursor.execute("""
            INSERT INTO summaries 
            (thread_id, summary_type, tldr, key_points, 
             important_changes, mentioned_subsystems, llm_model, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            thread_id,
            summary_type,
            summary_data.get('tldr', ''),
            key_points_json,
            important_changes_json,
            subsystems_json,
            summary_data.get('llm_model', ''),
            summary_data.get('generated_at', datetime.utcnow().isoformat())
        ))
        
        self.db.conn.commit()
    
    def _store_digest(self, date: str, digest_data: Dict):
        """Store daily digest in database"""
        cursor = self.db.conn.cursor()
        
        # Store as special summary with thread_id = NULL
        key_points_json = json.dumps(digest_data.get('highlights', []))
        
        important_changes = {
            'by_subsystem': digest_data.get('by_subsystem', {}),
            'hot_topics': digest_data.get('hot_topics', []),
            'critical_items': digest_data.get('critical_items', []),
            'statistics': digest_data.get('statistics', {})
        }
        important_changes_json = json.dumps(important_changes)
        
        cursor.execute("""
            INSERT INTO summaries 
            (thread_id, summary_date, summary_type, tldr, key_points, 
             important_changes, llm_model, generated_at)
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date,
            'daily',
            digest_data.get('tldr', ''),
            key_points_json,
            important_changes_json,
            digest_data.get('llm_model', ''),
            digest_data.get('generated_at', datetime.utcnow().isoformat())
        ))
        
        self.db.conn.commit()
    
    def get_summary_stats(self) -> Dict:
        """Get statistics about summaries"""
        cursor = self.db.conn.cursor()
        
        stats = {}
        
        cursor.execute("""
            SELECT summary_type, COUNT(*) as count
            FROM summaries
            GROUP BY summary_type
        """)
        
        for row in cursor.fetchall():
            stats[f"{row['summary_type']}_summaries"] = row['count']
        
        cursor.execute("SELECT COUNT(*) FROM threads")
        stats['total_threads'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM threads t
            WHERE EXISTS (
                SELECT 1 FROM summaries s 
                WHERE s.thread_id = t.id AND s.summary_type = 'thread'
            )
        """)
        stats['summarized_threads'] = cursor.fetchone()[0]
        
        return stats
