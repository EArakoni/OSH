#!/usr/bin/env python3
"""Quick database viewer with Gemini API summarization"""
import sqlite3
import json
import os
from tabulate import tabulate  # pip install tabulate if you want pretty tables
import google.generativeai as genai  # pip install google-generativeai

def setup_gemini():
    """Setup Gemini API - reads key from environment variable"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("\n⚠️  WARNING: GEMINI_API_KEY not found in environment variables")
        print("   Set it with: export GEMINI_API_KEY='your-api-key-here'")
        print("   Get your API key from: https://makersuite.google.com/app/apikey")
        print("   Running WITHOUT AI summaries...\n")
        return None
    
    try:
        genai.configure(api_key=api_key)
        
        # Try different model names that might be available
        model_names = [
            'gemini-1.5-flash-latest',
            'gemini-1.5-flash',
            'gemini-1.5-pro-latest', 
            'gemini-1.5-pro',
            'models/gemini-1.5-flash-latest',
            'models/gemini-pro'
        ]
        
        # Try to list available models
        try:
            print("\n🔍 Checking available models...")
            available_models = genai.list_models()
            print("Available models:")
            for m in available_models:
                if 'generateContent' in m.supported_generation_methods:
                    print(f"   - {m.name}")
                    # Use the first available model
                    model_name = m.name
                    model = genai.GenerativeModel(model_name)
                    print(f"\n✅ Gemini API configured successfully (using {model_name})\n")
                    return model
        except Exception as e:
            print(f"   Could not list models: {e}")
            print("   Trying default model names...")
        
        # Fallback: try each model name
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                # Test it with a simple prompt
                response = model.generate_content("Say 'test' if you can read this.")
                print(f"\n✅ Gemini API configured successfully (using {model_name})\n")
                return model
            except Exception as e:
                continue
        
        print("\n❌ Could not find a working Gemini model")
        print("   Running WITHOUT AI summaries...\n")
        return None
        
    except Exception as e:
        print(f"\n❌ Error configuring Gemini API: {e}")
        print("   Running WITHOUT AI summaries...\n")
        return None

def summarize_with_gemini(model, content, content_type="thread"):
    """Use Gemini to summarize content"""
    if not model:
        return "❌ Gemini API not configured"
    
    try:
        if content_type == "thread":
            prompt = f"""Summarize this email thread in 2-3 sentences, focusing on the main topic and key points:

{content}"""
        elif content_type == "email":
            prompt = f"""Provide a brief 1-2 sentence summary of this email:

{content}"""
        else:
            prompt = f"""Summarize the following database statistics and trends:

{content}"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error generating summary: {str(e)}"

def get_thread_content(cursor, thread_id, limit=5):
    """Get emails from a thread for summarization"""
    # First, get the thread subject to find related emails
    cursor.execute("SELECT subject FROM threads WHERE id = ?", (thread_id,))
    thread = cursor.fetchone()
    if not thread:
        return "No thread content found"
    
    thread_subject = thread['subject']
    
    # Find emails with matching or similar subjects (common in email threads)
    # Remove common prefixes like "Re:", "Fwd:", etc.
    import re
    clean_subject = re.sub(r'^(Re:|Fwd:|RE:|FW:|\[PATCH.*?\])\s*', '', thread_subject, flags=re.IGNORECASE).strip()
    
    cursor.execute("""
        SELECT subject, from_address, date, body
        FROM emails
        WHERE subject LIKE ? OR subject LIKE ?
        ORDER BY date
        LIMIT ?
    """, (f"%{clean_subject}%", thread_subject, limit))
    
    emails = cursor.fetchall()
    if not emails:
        # Fallback: just get any recent emails
        cursor.execute("""
            SELECT subject, from_address, date, body
            FROM emails
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        emails = cursor.fetchall()
    
    content = []
    for email in emails:
        content.append(f"From: {email['from_address']}\nDate: {email['date']}\n\n{email['body'][:500]}")
    
    return "\n\n---\n\n".join(content)

def view_database(db_path='lkml.db', use_gemini=True):
    """View database with optional Gemini summarization"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Setup Gemini
    model = setup_gemini() if use_gemini else None
    
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
    
    # AI Summary of database trends
    if model:
        print("\n🤖 AI OVERVIEW:")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                COUNT(*) as count
            FROM emails
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """)
        monthly_data = cursor.fetchall()
        stats_text = f"Database has {email_count} emails across {thread_count} threads from {sender_count} unique senders.\n"
        stats_text += "Monthly activity:\n" + "\n".join([f"{row['month']}: {row['count']} emails" for row in monthly_data])
        summary = summarize_with_gemini(model, stats_text, "overview")
        print(f"{summary}\n")
    
    # Show recent emails
    print("\n" + "="*80)
    print("RECENT EMAILS")
    print("="*80)
    
    cursor.execute("""
        SELECT id, subject, from_address, date, body
        FROM emails
        ORDER BY date DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"\n{row['id']}. {row['subject']}")
        print(f"   From: {row['from_address']}")
        print(f"   Date: {row['date']}")
        
        if model:
            email_summary = summarize_with_gemini(model, row['body'], "email")
            print(f"   💡 AI Summary: {email_summary}")
    
    # Show threads with summaries
    print("\n" + "="*80)
    print("TOP THREADS")
    print("="*80)
    
    cursor.execute("""
        SELECT id, subject, email_count, participant_count
        FROM threads
        ORDER BY email_count DESC
        LIMIT 3
    """)
    
    for row in cursor.fetchall():
        print(f"\n{row['id']}. {row['subject']}")
        print(f"   Emails: {row['email_count']}, Participants: {row['participant_count']}")
        
        if model:
            thread_content = get_thread_content(cursor, row['id'])
            thread_summary = summarize_with_gemini(model, thread_content, "thread")
            print(f"   💡 AI Thread Summary:")
            print(f"      {thread_summary}\n")
    
    # Show sample email body
    """print("\n" + "="*80)
    print("SAMPLE EMAIL BODY")
    print("="*80)
    
    cursor.execute("SELECT subject, body FROM emails LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"\nSubject: {row['subject']}")
        print(f"\nBody:\n{row['body'][:500]}...")"""
    
    conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='View database with optional Gemini AI summaries')
    parser.add_argument('--db', default='lkml.db', help='Database path (default: lkml.db)')
    parser.add_argument('--no-ai', action='store_true', help='Disable Gemini AI summaries')
    
    args = parser.parse_args()
    
    view_database(args.db, use_gemini=not args.no_ai)