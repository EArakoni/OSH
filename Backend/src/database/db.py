import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any

class Database:
    """Handles all database operations for LKML dashboard"""
    
    def __init__(self, db_path: str = "lkml.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create tables if they don't exist"""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema (SQLite allows multiple statements)
        self.conn.executescript(schema_sql)
        self.conn.commit()
        print(f"✅ Database initialized at {self.db_path}")
    
    def insert_email(self, email_data: Dict[str, Any]) -> int:
        """
        Insert an email into the database
        
        Args:
            email_data: Dictionary with email fields
            
        Returns:
            ID of inserted email (or existing if duplicate)
        """
        cursor = self.conn.cursor()
        
        try:
            # Handle both 'references' and 'references_list' keys
            references = email_data.get('references') or email_data.get('references_list', [])
            references_json = json.dumps(references)
            
            cursor.execute("""
                INSERT INTO emails 
                (message_id, subject, from_address, date, body, 
                 in_reply_to, references_list, raw_email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_data.get('message_id'),
                email_data.get('subject'),
                email_data.get('from'),
                email_data.get('date'),
                email_data.get('body'),
                email_data.get('in_reply_to'),
                references_json,
                email_data.get('raw', '')
            ))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.IntegrityError:
            # Email already exists (duplicate message_id)
            cursor.execute(
                "SELECT id FROM emails WHERE message_id = ?",
                (email_data.get('message_id'),)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_email_by_message_id(self, message_id: str) -> Optional[Dict]:
        """Get email by its Message-ID header"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM emails WHERE message_id = ?",
            (message_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_emails(self) -> List[Dict]:
        """Get all emails from database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM emails ORDER BY date DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def insert_thread(self, thread_data: Dict[str, Any]) -> int:
        """Insert a thread into the database"""
        cursor = self.conn.cursor()
        
        tags_json = json.dumps(thread_data.get('tags', []))
        
        try:
            cursor.execute("""
                INSERT INTO threads 
                (root_message_id, subject, participant_count, email_count,
                 first_post, last_post, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                thread_data.get('root_message_id'),
                thread_data.get('subject'),
                thread_data.get('participant_count', 0),
                thread_data.get('email_count', 0),
                thread_data.get('first_post'),
                thread_data.get('last_post'),
                tags_json
            ))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.IntegrityError:
            # Thread already exists, update it
            cursor.execute("""
                UPDATE threads 
                SET email_count = ?, last_post = ?
                WHERE root_message_id = ?
            """, (
                thread_data.get('email_count'),
                thread_data.get('last_post'),
                thread_data.get('root_message_id')
            ))
            self.conn.commit()
            
            cursor.execute(
                "SELECT id FROM threads WHERE root_message_id = ?",
                (thread_data.get('root_message_id'),)
            )
            return cursor.fetchone()[0]
    
    def link_email_to_thread(self, thread_id: int, email_id: int):
        """Link an email to a thread"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO thread_emails (thread_id, email_id)
                VALUES (?, ?)
            """, (thread_id, email_id))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already linked
    
    def search_emails(self, query: str) -> List[Dict]:
        """
        Full-text search across emails
        
        Args:
            query: Search query string
            
        Returns:
            List of matching emails
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT e.* 
            FROM emails e
            JOIN emails_fts fts ON e.id = fts.rowid
            WHERE emails_fts MATCH ?
            ORDER BY rank
        """, (query,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM emails")
        stats['total_emails'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM threads")
        stats['total_threads'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT from_address) FROM emails")
        stats['unique_senders'] = cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()
