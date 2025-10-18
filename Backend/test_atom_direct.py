#!/usr/bin/env python3
from src.parser.atom_parser import AtomParser
from src.parser.pipeline import LKMLPipeline
from src.parser.thread_builder import ThreadBuilder

# Parse your existing atom file
print("="*60)
print("Parsing new.atom")
print("="*60)

parser = AtomParser()
emails = parser.parse_atom_file('new.atom')

print(f"\n📊 Found {len(emails)} emails")
print("\nSample emails:")
for i, email in enumerate(emails[:3], 1):
    print(f"\n{i}. {email['subject']}")
    print(f"   From: {email['from']}")
    print(f"   Date: {email['date']}")

# Store in database
print("\n" + "="*60)
print("Storing in database")
print("="*60)

pipeline = LKMLPipeline("lkml.db")
try:
    email_ids = {}
    for idx, email in enumerate(emails):
        email_id = pipeline.db.insert_email(email)
        if email_id:
            email_ids[email['message_id']] = email_id
    
    print(f"✅ Stored {len(email_ids)} emails")
    
    # Build threads
    print("\nBuilding threads...")
    thread_builder = ThreadBuilder(emails)
    threads = thread_builder.build_threads()
    
    print(f"✅ Built {len(threads)} threads")
    
    # Show stats
    stats = pipeline.db.get_stats()
    print("\n" + "="*60)
    print("Database Statistics")
    print("="*60)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Success! Check lkml.db")
    
finally:
    pipeline.close()
