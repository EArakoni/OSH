#!/usr/bin/env python3
"""
Test the LKML parser pipeline with both mbox and Atom feeds
"""

import sys
from download_lkml import download_lkml_day, download_atom_feed
from src.parser.pipeline import LKMLPipeline
from src.parser.atom_parser import AtomParser

def test_atom_feed():
    """Test parsing an Atom feed"""
    print("="*60)
    print("Testing with Atom Feed")
    print("="*60)
    
    # Download latest feed
    atom_file = download_atom_feed()
    if not atom_file:
        print("❌ Failed to download Atom feed")
        return
    
    # Parse the Atom feed
    parser = AtomParser()
    emails = parser.parse_atom_file(atom_file)
    
    if not emails:
        print("❌ No emails parsed")
        return
    
    # Store in database
    pipeline = LKMLPipeline("lkml.db")
    try:
        print("\nStoring emails in database...")
        email_ids = {}
        
        for idx, email in enumerate(emails):
            email_id = pipeline.db.insert_email(email)
            if email_id:
                email_ids[email['message_id']] = email_id
            
            if (idx + 1) % 10 == 0:
                print(f"  Stored {idx + 1} emails...")
        
        print(f"✅ Stored {len(email_ids)} emails")
        
        # Build threads
        print("\nBuilding threads...")
        from src.parser.thread_builder import ThreadBuilder
        thread_builder = ThreadBuilder(emails)
        threads = thread_builder.build_threads()
        
        print(f"✅ Built {len(threads)} threads")
        
        # Show stats
        stats = pipeline.db.get_stats()
        print("\n" + "="*60)
        print("Database Statistics:")
        print("="*60)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    finally:
        pipeline.close()

def test_mbox(date: str):
    """Test parsing an mbox file"""
    print("="*60)
    print("Testing with mbox format")
    print("="*60)
    
    mbox_file = download_lkml_day(date)
    
    if not mbox_file:
        print("❌ Download failed")
        return
    
    pipeline = LKMLPipeline("lkml.db")
    
    try:
        pipeline.process_mbox(mbox_file)
    finally:
        pipeline.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_parser.py --atom              # Test with Atom feed")
        print("  python test_parser.py YYYY-MM-DD          # Test with mbox")
        print("\nExamples:")
        print("  python test_parser.py --atom")
        print("  python test_parser.py 2024-10-15")
        sys.exit(1)
    
    if sys.argv[1] == '--atom':
        test_atom_feed()
    else:
        date = sys.argv[1]
        test_mbox(date)
