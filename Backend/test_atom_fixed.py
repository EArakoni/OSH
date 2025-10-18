#!/usr/bin/env python3
from src.parser.atom_parser import AtomParser
from src.database.db import Database
from src.parser.thread_builder import ThreadBuilder

print("="*60)
print("Parsing new.atom")
print("="*60)

parser = AtomParser()
emails = parser.parse_atom_file('new.atom')

print(f"\n📊 Found {len(emails)} emails")

# Check for duplicate message IDs
message_ids = [e['message_id'] for e in emails]
unique_ids = set(message_ids)
print(f"   Unique message IDs: {len(unique_ids)}")

if len(message_ids) != len(unique_ids):
    print("⚠️  Warning: Duplicate message IDs found!")
    from collections import Counter
    duplicates = [id for id, count in Counter(message_ids).items() if count > 1]
    print(f"   Duplicates: {duplicates}")

print("\n" + "="*60)
print("Storing in database")
print("="*60)

db = Database("lkml-fixed.db")

email_ids = {}
success_count = 0
error_count = 0

for idx, email in enumerate(emails):
    try:
        email_id = db.insert_email(email)
        if email_id:
            email_ids[email['message_id']] = email_id
            success_count += 1
            print(f"  ✅ {idx+1}/{len(emails)}: {email['subject'][:60]}...")
        else:
            print(f"  ⚠️  {idx+1}/{len(emails)}: Returned None (might be duplicate)")
    except Exception as e:
        error_count += 1
        print(f"  ❌ {idx+1}/{len(emails)}: Error - {e}")
        print(f"     Subject: {email.get('subject', 'N/A')}")
        print(f"     Message ID: {email.get('message_id', 'N/A')}")

print(f"\n✅ Successfully stored: {success_count}")
print(f"❌ Errors: {error_count}")
print(f"📊 Total in email_ids dict: {len(email_ids)}")

# Verify what's actually in the database
cursor = db.conn.cursor()
cursor.execute("SELECT COUNT(*) FROM emails")
db_count = cursor.fetchone()[0]
print(f"📊 Actually in database: {db_count}")

if db_count != success_count:
    print(f"\n⚠️  MISMATCH: Expected {success_count} but found {db_count}")

# Show what's in the database
print("\n" + "="*60)
print("Emails in database:")
print("="*60)

cursor.execute("SELECT id, subject, from_address FROM emails")
for row in cursor.fetchall():
    print(f"{row[0]}. {row[1]}")
    print(f"   From: {row[2]}")

db.close()
print("\n✅ Done! Check lkml-fixed.db")
