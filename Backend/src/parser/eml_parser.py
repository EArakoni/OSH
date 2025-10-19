#!/usr/bin/env python3
"""
Parse .eml email files (standard email format)
Works with emails saved from Gmail, Thunderbird, Outlook, etc.
"""

import email
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class EMLParser:
    """Parse .eml email files"""
    
    def parse_eml_file(self, eml_path: str) -> Dict:
        """
        Parse a single .eml file
        
        Args:
            eml_path: Path to .eml file
            
        Returns:
            Email dictionary compatible with existing database schema
        """
        print(f"📧 Parsing .eml file: {eml_path}")
        
        if not Path(eml_path).exists():
            raise FileNotFoundError(f"EML file not found: {eml_path}")
        
        # Read and parse the .eml file
        with open(eml_path, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
        
        # Extract headers
        message_id = self._clean_message_id(msg.get('Message-ID', ''))
        subject = self._decode_header(msg.get('Subject', ''))
        from_addr = self._decode_header(msg.get('From', ''))
        date_str = msg.get('Date', '')
        
        # Parse date
        date_iso = self._parse_date(date_str)
        
        # Extract threading info
        in_reply_to = self._clean_message_id(msg.get('In-Reply-To', ''))
        references = self._parse_references(msg.get('References', ''))
        
        # Extract body
        body = self._extract_body(msg)
        
        email_data = {
            'message_id': message_id,
            'subject': subject,
            'from': from_addr,
            'date': date_iso,
            'in_reply_to': in_reply_to,
            'references': references,
            'body': body,
            'raw': str(msg)[:1000]
        }
        
        print(f"✅ Parsed email: {subject[:60]}...")
        return email_data
    
    def parse_digest_eml(self, filepath):
        """Parse LKML multipart/digest .eml file into individual emails."""
        with open(filepath, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)

        emails = []

        # Detect multipart/digest (typical LKML digest format)
        if msg.get_content_type() == 'multipart/digest':
            print("📦 Detected multipart/digest format")

            # Each part in multipart/digest is one embedded email
            for part in msg.iter_parts():
                if part.get_content_type() == 'message/rfc822':
                    # Proper embedded email — parse it as a new message
                    for submsg in part.iter_parts():
                        emails.append(submsg)
                elif part.get_content_type() == 'text/plain':
                    # Skip "Topics" summary text
                    text_payload = part.get_content()
                    if "Topics (" in text_payload[:100]:
                        print("📝 Skipping digest topic summary")
                    else:
                        # Sometimes plain text parts are actual messages (rare)
                        emails.append(part)

        else:
            # Not multipart/digest — single message
            emails.append(msg)

        print(f"✅ Extracted {len(emails)} sub-emails from digest")
        return emails

    def _split_digest(self, digest_email: Dict) -> List[Dict]:
        """
        Attempt to split a digest into individual emails
        
        This is heuristic-based and may not be perfect.
        """
        body = digest_email['body']
        emails = []
        
        # Try to find individual message boundaries
        # Common patterns: "Message: X", "From: ...", dividers
        
        # Simple approach: split on major dividers
        sections = body.split('----------------------------------------------------------------------')
        
        base_date = digest_email['date']
        
        for idx, section in enumerate(sections):
            if len(section.strip()) < 50:  # Skip tiny sections
                continue
            
            # Try to extract subject and from
            lines = section.strip().split('\n')
            subject = None
            from_addr = None
            
            for line in lines[:20]:  # Check first 20 lines
                if line.startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.startswith('From:'):
                    from_addr = line.replace('From:', '').strip()
            
            # Create email entry
            email_entry = {
                'message_id': f"{digest_email['message_id']}-part-{idx}",
                'subject': subject or f"Digest part {idx}",
                'from': from_addr or 'Unknown',
                'date': base_date,
                'in_reply_to': '',
                'references': [],
                'body': section.strip(),
                'raw': section[:1000]
            }
            
            emails.append(email_entry)
        
        if len(emails) > 1:
            print(f"✅ Split digest into {len(emails)} emails")
        else:
            print("ℹ️  Could not split digest, treating as single email")
            emails = [digest_email]
        
        return emails
    
    def _clean_message_id(self, message_id: str) -> str:
        """Clean Message-ID by removing < > brackets"""
        if not message_id:
            # Generate a unique ID if missing
            from hashlib import sha256
            from datetime import datetime
            unique_str = f"{datetime.utcnow().isoformat()}"
            return sha256(unique_str.encode()).hexdigest()[:16]
        return message_id.strip().strip('<>')
    
    def _decode_header(self, header: str) -> str:
        """Decode email header (handles encoding)"""
        if not header:
            return ''
        
        try:
            decoded_parts = email.header.decode_header(header)
            decoded_str = ''
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_str += part
            
            return decoded_str
        except:
            return str(header)
    
    def _parse_date(self, date_str: str) -> str:
        """Parse email date to ISO format"""
        if not date_str:
            return datetime.utcnow().isoformat()
        
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return date_str
    
    def _parse_references(self, references_str: str) -> List[str]:
        """Parse References header into list of message IDs"""
        if not references_str:
            return []
        
        import re
        message_ids = re.findall(r'<([^>]+)>', references_str)
        return message_ids
    
    def _extract_body(self, msg: email.message.Message) -> str:
        """Extract email body text"""
        body_parts = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                
                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            text = payload.decode('utf-8', errors='ignore')
                            body_parts.append(text)
                    except:
                        continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body_parts.append(payload.decode('utf-8', errors='ignore'))
            except:
                pass
        
        return '\n\n'.join(body_parts) if body_parts else ''


# Quick test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python eml_parser.py <path-to-eml-file>")
        sys.exit(1)
    
    parser = EMLParser()
    
    # Try as single email
    email_data = parser.parse_eml_file(sys.argv[1])
    
    print("\n" + "="*60)
    print("Parsed Email")
    print("="*60)
    print(f"Subject: {email_data['subject']}")
    print(f"From: {email_data['from']}")
    print(f"Date: {email_data['date']}")
    print(f"Message-ID: {email_data['message_id']}")
    print(f"Body length: {len(email_data['body'])} chars")
    print(f"\nBody preview:\n{email_data['body'][:500]}...")
