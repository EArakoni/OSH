#!/usr/bin/env python3
"""
LKML Dashboard - Main entry point

This script provides a CLI interface for the LKML parser
"""

import argparse
from src.parser.pipeline import LKMLPipeline
from src.database.db import Database
from download_lkml import download_lkml_day
import json

def download_and_process(date: str, db_path: str):
    """Download and process LKML for a specific date"""
    print(f"🔄 Processing LKML for {date}")
    
    # Download
    mbox_file = download_lkml_day(date)
    if not mbox_file:
        return
    
    # Process
    pipeline = LKMLPipeline(db_path)
    try:
        pipeline.process_mbox(mbox_file)
    finally:
        pipeline.close()

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

def main():
    parser = argparse.ArgumentParser(
        description="LKML Dashboard - Linux Kernel Mailing List Parser and Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and process today's LKML
  python main.py download 2024-10-18
  
  # Process an existing mbox file
  python main.py process lkml-2024-10-18.mbox
  
  # Show database statistics
  python main.py stats
  
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
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download and process LKML for a date')
    download_parser.add_argument('date', help='Date in YYYY-MM-DD format')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process an existing mbox file')
    process_parser.add_argument('mbox_file', help='Path to mbox file')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
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
    if args.command == 'download':
        download_and_process(args.date, args.db)
    elif args.command == 'process':
        process_existing(args.mbox_file, args.db)
    elif args.command == 'stats':
        show_stats(args.db)
    elif args.command == 'search':
        search_emails(args.query, args.db)
    elif args.command == 'export':
        export_threads(args.db, args.output)

if __name__ == "__main__":
    main()
