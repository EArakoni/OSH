from pathlib import Path
from src.database.db import Database
from src.parser.email_parser import EmailParser
from src.parser.thread_builder import ThreadBuilder

class LKMLPipeline:
    """
    Main pipeline for processing LKML emails
    
    Steps:
    1. Parse mbox file -> extract emails
    2. Store emails in database
    3. Build thread structure
    4. Store threads in database
    """
    
    def __init__(self, db_path: str = "lkml.db"):
        """Initialize pipeline with database"""
        self.db = Database(db_path)
        self.parser = EmailParser()
    
    def process_mbox(self, mbox_path: str):
        """
        Process an mbox file end-to-end
        
        Args:
            mbox_path: Path to mbox file
        """
        print(f"\n{'='*60}")
        print(f"🚀 Starting LKML Pipeline")
        print(f"{'='*60}\n")
        
        # Step 1: Parse emails from mbox
        print("Step 1: Parsing emails...")
        emails = self.parser.parse_mbox_file(mbox_path)
        
        if not emails:
            print("❌ No emails found in mbox file")
            return
        
        # Step 2: Store emails in database
        print(f"\nStep 2: Storing {len(emails)} emails in database...")
        email_ids = {}  # Map message_id -> database id
        
        for idx, email in enumerate(emails):
            email_id = self.db.insert_email(email)
            if email_id:
                email_ids[email['message_id']] = email_id
            
            if (idx + 1) % 100 == 0:
                print(f"  Stored {idx + 1} emails...")
        
        print(f"✅ Stored {len(email_ids)} emails")
        
        # Step 3: Build threads
        print("\nStep 3: Building threads...")
        thread_builder = ThreadBuilder(emails)
        threads = thread_builder.build_threads()
        
        # Step 4: Store threads
        print(f"\nStep 4: Storing {len(threads)} threads...")
        
        for root_id, thread_emails in threads.items():
            # Get thread metadata
            thread_meta = thread_builder.get_thread_metadata(thread_emails)
            
            # Insert thread
            thread_id = self.db.insert_thread(thread_meta)
            
            # Link emails to thread
            for email in thread_emails:
                email_db_id = email_ids.get(email['message_id'])
                if email_db_id:
                    self.db.link_email_to_thread(thread_id, email_db_id)
        
        print("✅ Threads stored successfully")
        
        # Print statistics
        print(f"\n{'='*60}")
        print("📊 Pipeline Statistics:")
        print(f"{'='*60}")
        
        stats = self.db.get_stats()
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n{'='*60}")
        print("✅ Pipeline completed successfully!")
        print(f"{'='*60}\n")
    
    def close(self):
        """Close database connection"""
        self.db.close()

# Usage example
if __name__ == "__main__":
    pipeline = LKMLPipeline()
    
    try:
        # Process an mbox file
        pipeline.process_mbox("lkml-2024-10-18.mbox")
    finally:
        pipeline.close()
