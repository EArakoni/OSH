#!/usr/bin/env python3
"""
Quick test script for Gemini integration
"""

import os
import sys

def test_gemini_basic():
    """Test basic Gemini connectivity"""
    print("="*60)
    print("Testing Gemini Integration")
    print("="*60)
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        print("\nSet it with:")
        print("  export GEMINI_API_KEY='your-key-here'")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Try importing
    try:
        from src.llm.gemini_client import GeminiClient
        print("✅ GeminiClient import successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nInstall with:")
        print("  pip install google-generativeai")
        return False
    
    # Try creating client
    try:
        client = GeminiClient(api_key=api_key)
        print(f"✅ Client initialized: {client.model_name}")
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        print("\nTrying to list available models...")
        try:
            from src.llm.gemini_client import GeminiClient
            GeminiClient.list_available_models()
        except:
            pass
        return False
    
    # Try a simple summary
    print("\n" + "="*60)
    print("Testing Email Summarization")
    print("="*60)
    
    test_email = {
        'message_id': 'test@example.com',
        'subject': '[PATCH] Fix memory leak in network driver',
        'from': 'John Developer <john@kernel.org>',
        'body': """This patch fixes a memory leak in the e1000 network driver
that was causing issues under high load. The leak was in the buffer
allocation code where we weren't properly freeing buffers on error paths.

The fix adds proper cleanup on all error paths and has been tested
with network stress tests.""",
        'date': '2025-10-18T10:00:00Z'
    }
    
    try:
        print("\nSummarizing test email...")
        result = client.summarize_email(test_email)
        
        print(f"\n✅ Summary generated!")
        print(f"   TL;DR: {result.get('tldr', 'N/A')}")
        print(f"   Type: {result.get('email_type', 'N/A')}")
        print(f"   Subsystems: {result.get('subsystems', [])}")
        print(f"   Importance: {result.get('importance', 'N/A')}")
        
        if result.get('key_points'):
            print("\n   Key Points:")
            for point in result['key_points']:
                print(f"     - {point}")
        
        return True
        
    except Exception as e:
        print(f"❌ Summarization failed: {e}")
        return False

def test_with_real_data():
    """Test summarization with real database"""
    print("\n" + "="*60)
    print("Testing with Real Database")
    print("="*60)
    
    from src.database.db import Database
    from src.llm.gemini_client import GeminiClient
    from src.llm.summarizer import LKMLSummarizer
    
    db_path = 'lkml.db'
    
    if not os.path.exists(db_path):
        print(f"⚠️  Database not found: {db_path}")
        print("   Run: python main.py atom new.atom")
        return False
    
    db = Database(db_path)
    
    try:
        # Check if we have threads
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM threads WHERE email_count >= 2")
        thread_count = cursor.fetchone()[0]
        
        if thread_count == 0:
            print("⚠️  No threads with 2+ emails found")
            return False
        
        print(f"✅ Found {thread_count} threads to test with")
        
        # Get first thread
        cursor.execute("""
            SELECT id, subject, email_count 
            FROM threads 
            WHERE email_count >= 2 
            LIMIT 1
        """)
        thread = cursor.fetchone()
        
        print(f"\nTest thread: {thread['subject']}")
        print(f"Emails in thread: {thread['email_count']}")
        
        # Try summarizing
        api_key = os.getenv('GEMINI_API_KEY')
        gemini = GeminiClient(api_key=api_key)
        summarizer = LKMLSummarizer(db, gemini)
        
        print("\nGenerating summary...")
        summary = summarizer.summarize_thread(thread['id'])
        
        if summary and not summary.get('error'):
            print("✅ Summary generated successfully!")
            print(f"\nTL;DR: {summary.get('tldr', 'N/A')}")
            
            if summary.get('key_points'):
                print("\nKey Points:")
                for point in summary['key_points']:
                    print(f"  - {point}")
            
            return True
        else:
            print(f"❌ Summary failed: {summary.get('error', 'Unknown error')}")
            return False
            
    finally:
        db.close()

def main():
    """Run all tests"""
    print("\n🧪 LKML Dashboard - Gemini Integration Test Suite\n")
    
    # Test 1: Basic connectivity
    test1_passed = test_gemini_basic()
    
    if not test1_passed:
        print("\n❌ Basic test failed. Fix issues before continuing.")
        return
    
    # Test 2: Real data (optional)
    print("\n" + "="*60)
    user_input = input("Test with real database? (y/n): ").strip().lower()
    
    if user_input == 'y':
        test2_passed = test_with_real_data()
        
        if test2_passed:
            print("\n" + "="*60)
            print("🎉 All tests passed!")
            print("="*60)
            print("\nYou're ready to use Gemini summarization!")
            print("\nNext steps:")
            print("  1. python main.py summarize --limit 5")
            print("  2. python main.py show-summary --thread 1")
            print("  3. python main.py digest --date 2025-10-18")
        else:
            print("\n⚠️  Real data test failed")
    else:
        print("\n✅ Basic tests passed! Skipping real data test.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
