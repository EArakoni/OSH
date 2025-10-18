#!/usr/bin/env python3
from src.parser.atom_parser import AtomParser
from src.database.db import Database
from src.parser.thread_builder import ThreadBuilder
import json

print("="*60)
print("Parsing new.atom")
print("="*60)

parser = AtomParser()
emails = parser.parse_atom_file('new.atom')

print(f"\n📊 Found {len(emails)} emails")

# Debug: Check first email structure
print("\nFirst email structure:")
first = emails[0]
for key, value in first.items():
    if key == 'body':
        print(f"  {key}: {str(value)[:100]}...")
    else:
        print(f"  {key}: {value}")

print("\n" + "="*60)
print("Creating database")
print("="*60)

# Create database and insert one email to test
db = Database("lkml-debug.db")

print("\nInserting first email...")
try:
    email_id = db.insert_email(first)
    print(f"✅ Successfully inserted email with ID: {email_id}")
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"\nEmail data being inserted:")
    print(json.dumps({k: str(v)[:100] if k == 'body' else v for k, v in first.items()}, indent=2))

db.close()
