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
from download_lkml import download_lkml_day, download_atom_feed
import json
# Import Gemini components (with graceful fallback)
try:
    from src.llm.gemini_client import GeminiClient
    from src.llm.summarizer import LKMLSummarizer
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Gemini summarization not available. Install: pip install google-generativeai")

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

def main():
    parser = argparse.ArgumentParser(
        description="LKML Dashboard - Linux Kernel Mailing List Parser and Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process an Atom feed (recommended for testing)
  python main.py atom new.atom
  
  # Download and process a specific day (mbox format)
  python main.py download 2024-10-15
  
  # Process an existing mbox file
  python main.py process lkml-2024-10-18.mbox
  
  # Show database statistics
  python main.py stats
  
  # Show sample emails
  python main.py sample
  
  # Search emails
  python main.py search "memory leak"
  
  # Export threads to JSON
  python main.py export threads.json
        """
    )
    
    parser.add_argument(
        '--db',
        default='lkml.db',
        help='Database path (default: lkml.db)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Atom command (NEW!)
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
    
    # Sample command (NEW!)
    sample_parser = subparsers.add_parser('sample', help='Show sample emails')
    sample_parser.add_argument('-n', '--count', type=int, default=5, help='Number of emails to show')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search emails')
    search_parser.add_argument('query', help='Search query')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export threads to JSON')
    export_parser.add_argument('output', help='Output JSON file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'atom':
        process_atom_feed(args.atom_file, args.db)
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

if __name__ == "__main__":
    main()
