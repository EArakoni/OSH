import mailbox
import email
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional
import re
from pathlib import Path

class EmailParser:
    """Parses LKML emails from mbox files"""
    
    def __init__(self):
        """Initialize the email parser"""
        pass
    
    def parse_mbox_file(self, mbox_path: str) -> List[Dict]:
        """
        Parse an mbox file and extract all emails
        
        Args:
            mbox_path: Path to .mbox file
            
        Returns:
            List of email dictionaries
        
        Steps:
        1. Open mbox file (standard Unix mailbox format)
        2. Iterate through each message
        3. Extract headers and body
        4. Return structured data
        """
        print(f"📧 Parsing mbox file: {mbox_path}")
        
        if not Path(mbox_path).exists():
            raise FileNotFoundError(f"Mbox file not found: {mbox_path}")
        
        mbox = mailbox.mbox(mbox_path)
        emails = []
        
        for idx, message in enumerate(mbox):
            try:
                email_data = self._parse_message(message)
                emails.append(email_data)
                
                if (idx + 1) % 100 == 0:
                    print(f"  Parsed {idx + 1} emails...")
                    
            except Exception as e:
                print(f"  ⚠️  Error parsing email {idx}: {e}")
                continue
        
        print(f"✅ Parsed {len(emails)} emails from {mbox_path}")
        return emails
    
    def _parse_message(self, message: email.message.Message) -> Dict:
        """
        Parse a single email message
        
        Args:
            message: Email message object
            
        Returns:
            Dictionary with parsed email data
            
        Steps:
        1. Extract Message-ID (unique identifier)
        2. Extract subject, from, to, date
        3. Extract threading info (In-Reply-To, References)
        4. Extract body content
        5. Clean and structure the data
        """
        # Extract basic headers
        message_id = self._clean_message_id(message.get('Message-ID', ''))
        subject = self._decode_header(message.get('Subject', ''))
        from_addr = self._decode_header(message.get('From', ''))
        date_str = message.get('Date', '')
        
        # Parse date to ISO format
        date_iso = self._parse_date(date_str)
        
        # Extract threading information
        in_reply_to = self._clean_message_id(message.get('In-Reply-To', ''))
        references = self._parse_references(message.get('References', ''))
        
        # Extract body
        body = self._extract_body(message)
        
        return {
            'message_id': message_id,
            'subject': subject,
            'from': from_addr,
            'date': date_iso,
            'in_reply_to': in_reply_to,
            'references': references,
            'body': body,
            'raw': str(message)[:1000]  # Store first 1000 chars for debugging
        }
    
    def _clean_message_id(self, message_id: str) -> str:
        """
        Clean Message-ID by removing < > brackets
        
        Example: <abc123@kernel.org> -> abc123@kernel.org
        """
        if not message_id:
            return ''
        return message_id.strip().strip('<>')
    
    def _decode_header(self, header: str) -> str:
        """
        Decode email header (handles encoding)
        
        Email headers can be encoded (e.g., =?UTF-8?B?...?=)
        This function decodes them to plain text
        """
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
            return header
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parse email date to ISO format
        
        Example: "Mon, 18 Oct 2024 10:30:00 -0400" -> "2024-10-18T10:30:00-04:00"
        """
        if not date_str:
            return ''
        
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return date_str
    
    def _parse_references(self, references_str: str) -> List[str]:
        """
        Parse References header into list of message IDs
        
        References are space-separated message IDs showing email thread history
        Example: "<id1@example.com> <id2@example.com>" -> ["id1@example.com", "id2@example.com"]
        """
        if not references_str:
            return []
        
        # Split by whitespace and clean each ID
        message_ids = re.findall(r'<([^>]+)>', references_str)
        return message_ids
    
    def _extract_body(self, message: email.message.Message) -> str:
        """
        Extract email body text
        
        Emails can be:
        - Plain text (simple)
        - Multipart (has attachments, HTML, etc.)
        
        We want the plain text part
        """
        if message.is_multipart():
            # Email has multiple parts (text, HTML, attachments)
            # We only want text/plain parts
            body_parts = []
            
            for part in message.walk():
                content_type = part.get_content_type()
                
                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            text = payload.decode('utf-8', errors='ignore')
                            body_parts.append(text)
                    except:
                        continue
            
            return '\n'.join(body_parts)
        else:
            # Simple plain text email
            try:
                payload = message.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='ignore')
            except:
                pass
        
        return ''
    
    def extract_patch_info(self, body: str) -> Optional[Dict]:
        """
        Extract patch information if email contains a patch
        
        LKML emails often contain patches with format:
        ---
         file.c | 10 ++++------
         1 file changed, 4 insertions(+), 6 deletions(-)
        
        This is optional but useful for categorization
        """
        if '---' not in body or 'diff' not in body.lower():
            return None
        
        # Simple detection - can be enhanced
        has_patch = bool(re.search(r'^---$', body, re.MULTILINE))
        files_changed = len(re.findall(r'\+\+\+ b/', body))
        
        return {
            'has_patch': has_patch,
            'files_changed': files_changed
        }
