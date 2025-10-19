#!/usr/bin/env python3
"""
LKML Dashboard - Main entry point
"""

import argparse
import os
import sys
from src.parser.pipeline import LKMLPipeline
from src.parser.atom_parser import AtomParser
from src.parser.thread_builder import ThreadBuilder
from src.database.db import Database
from src.parser.email_parser import EmailParser
from download_lkml import download_lkml_day, download_atom_feed
import json

# Import Gemini components (with graceful fallback)
try:
    from src.llm.gemini_client import GeminiClient
    from src.llm.summarizer import LKMLSummarizer
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Gemini summarization not available. Install: pip install google-generativeai tenacity")

def download_and_process(date: str, db_path: str):
    """Download and process LKML for a specific date"""
    print(f"🔄 Processing LKML for {date}")
    
    mbox_file = download_lkml_day(date)
    if not mbox_file:
        return
    
    pipeline = LKMLPipeline(db_path)
    try:
        pipeline.process_mbox(mbox_file)
    finally:
        pipeline.close()


def process_atom_feed(atom_file: str, db_path: str):
    """Process an Atom feed file"""
    print(f"🔄 Processing Atom feed: {atom_file}")
    
    # Parse the Atom feed
    parser = AtomParser()
    emails = parser.parse_atom_file(atom_file)
    
    if not emails:
        print("❌ No emails found in Atom feed")
        return
    
    # Store in database
    db = Database(db_path)
    
    try:
        print(f"\n📊 Storing {len(emails)} emails...")
        email_ids = {}
        success_count = 0
        
        for idx, email in enumerate(emails, 1):
            try:
                email_id = db.insert_email(email)
                if email_id:
                    email_ids[email['message_id']] = email_id
                    success_count += 1
                    if idx % 10 == 0:
                        print(f"  Stored {idx}/{len(emails)} emails...")
            except Exception as e:
                print(f"  ⚠️  Error storing email {idx}: {e}")
        
        print(f"✅ Successfully stored {success_count}/{len(emails)} emails")
        
        # Build threads
        print("\n🧵 Building threads...")
        thread_builder = ThreadBuilder(emails)
        threads = thread_builder.build_threads()
        
        print(f"  Found {len(threads)} threads")
        
        # Store threads
        print("  Storing thread metadata...")
        for root_id, thread_emails in threads.items():
            thread_meta = thread_builder.get_thread_metadata(thread_emails)
            thread_id = db.insert_thread(thread_meta)
            
            # Link emails to thread
            for email in thread_emails:
                email_db_id = email_ids.get(email['message_id'])
                if email_db_id:
                    db.link_email_to_thread(thread_id, email_db_id)
        
        print(f"✅ Thread building complete")
        
        # Show stats
        print("\n" + "="*60)
        print("📊 Database Statistics")
        print("="*60)
        stats = db.get_stats()
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value:,}")
        print("="*60)
        
    finally:
        db.close()

def process_existing(mbox_path: str, db_path: str):
    """Process an existing mbox file"""
    pipeline = LKMLPipeline(db_path)
    try:
        pipeline.process_mbox(mbox_path)
    finally:
        pipeline.close()

def show_stats(db_path: str):
    """Show database statistics"""
    with Database(db_path) as db:
        stats = db.get_stats()
        
        print("\n" + "="*60)
        print("📊 Database Statistics")
        print("="*60)
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value:,}")
        print("="*60 + "\n")

def search_emails(query: str, db_path: str):
    """Search emails by full-text search"""
    with Database(db_path) as db:
        results = db.search_emails(query)
        
        print(f"\n🔍 Search results for: '{query}'")
        print(f"Found {len(results)} matches\n")
        
        for idx, email in enumerate(results[:10], 1):
            print(f"{idx}. {email['subject']}")
            print(f"   From: {email['from_address']}")
            print(f"   Date: {email['date']}")
            print(f"   Preview: {email['body'][:100]}...")
            print()

def export_threads(db_path: str, output_file: str):
    """Export threads to JSON for analysis"""
    with Database(db_path) as db:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT t.*, COUNT(te.email_id) as email_count
            FROM threads t
            LEFT JOIN thread_emails te ON t.id = te.thread_id
            GROUP BY t.id
            ORDER BY t.last_post DESC
            LIMIT 100
        """)
        
        threads = [dict(row) for row in cursor.fetchall()]
        
        with open(output_file, 'w') as f:
            json.dump(threads, f, indent=2)
        
        print(f"✅ Exported {len(threads)} threads to {output_file}")

def process_eml_file(eml_file: str, db_path: str):
    """Process a single EML or digest EML file"""
    print(f"🔄 Processing EML file: {eml_file}")
    
    parser = EmailParser()

    # Parse the EML file (handles both single and digest)
    try:
        emails = parser.parse_eml_file(eml_file)
    except Exception as e:
        print(f"❌ Failed to parse EML file: {e}")
        import traceback
        traceback.print_exc()
        return

    if not emails:
        print("⚠️ No emails found in EML file.")
        return

    print(f"📨 Parsed {len(emails)} individual email(s) from file.")
    
    db = Database(db_path)
    email_ids = {}
    success_count = 0

    try:
        print(f"\n📊 Inserting {len(emails)} emails into database...")
        for idx, email in enumerate(emails, 1):
            try:
                email_id = db.insert_email(email)
                if email_id:
                    email_ids[email['message_id']] = email_id
                    success_count += 1
                    if idx % 10 == 0 or idx == len(emails):
                        print(f"  ✅ {idx}/{len(emails)} stored.")
            except Exception as e:
                print(f"  ⚠️ Error inserting email {idx}: {e}")

        print(f"✅ Successfully inserted {success_count}/{len(emails)} emails.")

        # Build threads
        print("\n🧵 Building threads...")
        thread_builder = ThreadBuilder(emails)
        threads = thread_builder.build_threads()
        print(f"  Found {len(threads)} threads")

        # Store threads
        for root_id, thread_emails in threads.items():
            try:
                thread_meta = thread_builder.get_thread_metadata(thread_emails)
                thread_id = db.insert_thread(thread_meta)
                for email in thread_emails:
                    email_db_id = email_ids.get(email['message_id'])
                    if email_db_id:
                        db.link_email_to_thread(thread_id, email_db_id)
            except Exception as e:
                print(f"  ⚠️ Error inserting thread: {e}")

        print("✅ Thread building complete.")

        # Stats
        print("\n" + "="*60)
        print("📊 Database Statistics")
        print("="*60)
        stats = db.get_stats()
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value:,}")
        print("="*60)

    finally:
        db.close()


def show_sample_emails(db_path: str, count: int = 5):
    """Show sample emails for testing"""
    with Database(db_path) as db:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, subject, from_address, 
                   substr(body, 1, 200) as body_preview
            FROM emails 
            ORDER BY date DESC 
            LIMIT ?
        """, (count,))
        
        print("\n" + "="*60)
        print(f"📧 Sample Emails (showing {count})")
        print("="*60)
        
        for row in cursor.fetchall():
            print(f"\nID: {row[0]}")
            print(f"Subject: {row[1]}")
            print(f"From: {row[2]}")
            print(f"Body: {row[3]}...")
            print("-" * 60)

# ============================================================================
# GEMINI COMMANDS
# ============================================================================

def summarize_threads(db_path: str, limit: int = None, min_emails: int = 2, 
                     force: bool = False, model: str = 'flash'):
    """Summarize threads using Gemini"""
    if not GEMINI_AVAILABLE:
        print("❌ Gemini not available. Install: pip install google-generativeai tenacity")
        return
    
    db = Database(db_path)
    client = GeminiClient(model=model)
    summarizer = LKMLSummarizer(db, client)
    
    try:
        stats = summarizer.summarize_all_threads(
            limit=limit,
            min_emails=min_emails,
            skip_errors=True
        )
        
        print(f"\n📊 Summarization complete!")
        print(f"   Success: {stats['success']}")
        print(f"   Errors: {stats['errors']}")
        
        client.print_metrics()
        summarizer.print_summary_stats()
        
    finally:
        db.close()

def show_thread_summary(db_path: str, thread_id: int):
    """Show summary for a specific thread"""
    db = Database(db_path)
    
    try:
        cursor = db.conn.cursor()
        
        # Get thread info
        cursor.execute("SELECT * FROM threads WHERE id = ?", (thread_id,))
        thread = cursor.fetchone()
        
        if not thread:
            print(f"❌ Thread {thread_id} not found")
            return
        
        thread_dict = dict(thread)
        
        # Get summary
        cursor.execute("""
            SELECT * FROM summaries 
            WHERE thread_id = ? AND summary_type = 'thread'
            ORDER BY generated_at DESC
            LIMIT 1
        """, (thread_id,))
        
        summary = cursor.fetchone()
        
        print("\n" + "="*60)
        print(f"Thread {thread_id}: {thread_dict['subject']}")
        print("="*60)
        print(f"Emails: {thread_dict['email_count']}")
        print(f"Participants: {thread_dict['participant_count']}")
        print(f"Date range: {thread_dict['first_post']} → {thread_dict['last_post']}")
        
        if summary:
            summary_dict = dict(summary)
            print("\n📝 SUMMARY:")
            print(f"   TL;DR: {summary_dict['tldr']}")
            
            if summary_dict.get('key_points'):
                key_points = json.loads(summary_dict['key_points'])
                print("\n   Key Points:")
                for point in key_points:
                    print(f"     • {point}")
            
            if summary_dict.get('mentioned_subsystems'):
                subsystems = json.loads(summary_dict['mentioned_subsystems'])
                print(f"\n   Subsystems: {', '.join(subsystems)}")
            
            print(f"\n   Generated: {summary_dict['generated_at']}")
            print(f"   Model: {summary_dict['llm_model']}")
        else:
            print("\n⚠️  No summary available")
            print("   Run: python main.py summarize --limit 1")
        
        print("="*60)
        
    finally:
        db.close()

def generate_digest(db_path: str, date: str, force: bool = False, model: str = 'flash'):
    """Generate daily digest"""
    if not GEMINI_AVAILABLE:
        print("❌ Gemini not available. Install: pip install google-generativeai tenacity")
        return
    
    db = Database(db_path)
    client = GeminiClient(model=model)
    summarizer = LKMLSummarizer(db, client)
    
    try:
        digest = summarizer.generate_daily_digest(date, force=force)
        
        if digest and not digest.get('error'):
            print("\n" + "="*60)
            print(f"📅 Daily Digest - {date}")
            print("="*60)
            print(f"\n{digest['tldr']}\n")
            
            if digest.get('highlights'):
                print("🌟 Highlights:")
                for highlight in digest['highlights']:
                    print(f"  • {highlight}")
            
            if digest.get('critical_items'):
                print("\n🚨 Critical Items:")
                for item in digest['critical_items']:
                    print(f"  • {item}")
            
            print("\n" + "="*60)
            
            client.print_metrics()
        else:
            print(f"❌ Failed to generate digest")
        
    finally:
        db.close()

def list_summaries(db_path: str, limit: int = 10):
    """List recent summaries"""
    if not GEMINI_AVAILABLE:
        print("❌ Gemini not available")
        return
    
    db = Database(db_path)
    summarizer = LKMLSummarizer(db, GeminiClient())
    
    try:
        summaries = summarizer.get_recent_summaries(limit=limit)
        
        print("\n" + "="*60)
        print(f"📋 Recent Summaries (last {limit})")
        print("="*60)
        
        for summary in summaries:
            print(f"\nThread: {summary.get('subject', 'N/A')}")
            print(f"TL;DR: {summary['tldr']}")
            print(f"Type: {summary['summary_type']} | Generated: {summary['generated_at']}")
            print("-" * 60)
        
        summarizer.print_summary_stats()
        
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(
        description="LKML Dashboard - Linux Kernel Mailing List Parser and Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Data ingestion
  python main.py atom new.atom
  python main.py eml digest.eml
  python main.py download 2024-10-15
  
  # Database queries
  python main.py stats
  python main.py sample -n 10
  python main.py search "memory leak"
  
  # Gemini summarization
  python main.py summarize --limit 5
  python main.py show-summary --thread 1
  python main.py digest --date 2025-10-18
  python main.py list-summaries
        """
    )
    
    parser.add_argument(
        '--db',
        default='lkml.db',
        help='Database path (default: lkml.db)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Atom command
    atom_parser = subparsers.add_parser('atom', help='Process an Atom feed file')
    atom_parser.add_argument('atom_file', help='Path to Atom XML file')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download and process LKML for a date')
    download_parser.add_argument('date', help='Date in YYYY-MM-DD format')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process an existing mbox file')
    process_parser.add_argument('mbox_file', help='Path to mbox file')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # Sample command
    sample_parser = subparsers.add_parser('sample', help='Show sample emails')
    sample_parser.add_argument('-n', '--count', type=int, default=5, help='Number of emails to show')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search emails')
    search_parser.add_argument('query', help='Search query')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export threads to JSON')
    export_parser.add_argument('output', help='Output JSON file')

    # EML command
    eml_parser = subparsers.add_parser('eml', help='Process a single EML or digest EML file')
    eml_parser.add_argument('eml_file', help='Path to .eml file or digest')
    
    # Summarize command
    summarize_parser = subparsers.add_parser('summarize', help='Summarize threads with Gemini')
    summarize_parser.add_argument('--limit', type=int, help='Max threads to summarize')
    summarize_parser.add_argument('--min-emails', type=int, default=2, help='Min emails per thread')
    summarize_parser.add_argument('--force', action='store_true', help='Regenerate existing summaries')
    summarize_parser.add_argument('--model', default='flash', choices=['flash', 'flash-8b', 'pro'], 
                                 help='Gemini model to use')
    
    # Show summary command
    show_summary_parser = subparsers.add_parser('show-summary', help='Show summary for a thread')
    show_summary_parser.add_argument('--thread', type=int, required=True, help='Thread ID')
    
    # Digest command
    digest_parser = subparsers.add_parser('digest', help='Generate daily digest')
    digest_parser.add_argument('--date', required=True, help='Date (YYYY-MM-DD)')
    digest_parser.add_argument('--force', action='store_true', help='Regenerate if exists')
    digest_parser.add_argument('--model', default='flash', choices=['flash', 'flash-8b', 'pro'])
    
    # List summaries command
    list_summaries_parser = subparsers.add_parser('list-summaries', help='List recent summaries')
    list_summaries_parser.add_argument('--limit', type=int, default=10, help='Number to show')

    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'atom':
        process_atom_feed(args.atom_file, args.db)
    elif args.command == 'eml':
        process_eml_file(args.eml_file, args.db)
    elif args.command == 'download':
        download_and_process(args.date, args.db)
    elif args.command == 'process':
        process_existing(args.mbox_file, args.db)
    elif args.command == 'stats':
        show_stats(args.db)
    elif args.command == 'sample':
        show_sample_emails(args.db, args.count)
    elif args.command == 'search':
        search_emails(args.query, args.db)
    elif args.command == 'export':
        export_threads(args.db, args.output)
    elif args.command == 'summarize':
        summarize_threads(args.db, args.limit, args.min_emails, args.force, args.model)
    elif args.command == 'show-summary':
        show_thread_summary(args.db, args.thread)
    elif args.command == 'digest':
        generate_digest(args.db, args.date, args.force, args.model)
    elif args.command == 'list-summaries':
        list_summaries(args.db, args.limit)

if __name__ == "__main__":
    main()
