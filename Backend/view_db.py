#!/usr/bin/env python3
"""Quick database viewer"""

import sqlite3
import json
from tabulate import tabulate  # pip install tabulate if you want pretty tables

def view_database(db_path='lkml.db'):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("="*80)
    print("DATABASE OVERVIEW")
    print("="*80)
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM emails")
    email_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM threads")
    thread_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT from_address) FROM emails")
    sender_count = cursor.fetchone()[0]
    
    print(f"\n📊 Statistics:")
    print(f"   Total Emails: {email_count}")
    print(f"   Total Threads: {thread_count}")
    print(f"   Unique Senders: {sender_count}")
    
    # Show recent emails
    print("\n" + "="*80)
    print("RECENT EMAILS")
    print("="*80)
    
    cursor.execute("""
        SELECT id, subject, from_address, date 
        FROM emails 
        ORDER BY date DESC 
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"\n{row['id']}. {row['subject']}")
        print(f"   From: {row['from_address']}")
        print(f"   Date: {row['date']}")
    
    # Show threads
    print("\n" + "="*80)
    print("THREADS")
    print("="*80)
    
    cursor.execute("""
        SELECT id, subject, email_count, participant_count
        FROM threads 
        ORDER BY email_count DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"\n{row['id']}. {row['subject']}")
        print(f"   Emails: {row['email_count']}, Participants: {row['participant_count']}")
    
    # Show sample email body
    print("\n" + "="*80)
    print("SAMPLE EMAIL BODY")
    print("="*80)
    
    cursor.execute("SELECT subject, body FROM emails LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"\nSubject: {row['subject']}")
        print(f"\nBody:\n{row['body'][:500]}...")
    
    conn.close()

if __name__ == "__main__":
    view_database()
