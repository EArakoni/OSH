import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict
import html

class AtomParser:
    """Parse LKML Atom feeds from lore.kernel.org"""
    
    # Atom namespace
    NS = {'atom': 'http://www.w3.org/2005/Atom',
          'thr': 'http://purl.org/syndication/thread/1.0'}
    
    def parse_atom_file(self, atom_path: str) -> List[Dict]:
        """
        Parse an Atom feed XML file
        
        Args:
            atom_path: Path to .atom XML file
            
        Returns:
            List of email dictionaries
        """
        print(f"📧 Parsing Atom feed: {atom_path}")
        
        tree = ET.parse(atom_path)
        root = tree.getroot()
        
        emails = []
        
        # Find all entry elements
        entries = root.findall('atom:entry', self.NS)
        
        for entry in entries:
            email_data = self._parse_entry(entry)
            if email_data:
                emails.append(email_data)
        
        print(f"✅ Parsed {len(emails)} emails from {atom_path}")
        return emails
    
    def _parse_entry(self, entry: ET.Element) -> Dict:
        """Parse a single Atom entry"""
        
        # Extract author
        author_elem = entry.find('atom:author', self.NS)
        author_name = ''
        author_email = ''
        if author_elem is not None:
            name_elem = author_elem.find('atom:name', self.NS)
            email_elem = author_elem.find('atom:email', self.NS)
            author_name = name_elem.text if name_elem is not None else ''
            author_email = email_elem.text if email_elem is not None else ''
        
        from_addr = f"{author_name} <{author_email}>" if author_name and author_email else author_email
        
        # Extract other fields
        title = entry.find('atom:title', self.NS)
        subject = title.text if title is not None else ''
        
        updated = entry.find('atom:updated', self.NS)
        date_str = updated.text if updated is not None else ''
        
        # Extract message ID from id element
        id_elem = entry.find('atom:id', self.NS)
        message_id = ''
        if id_elem is not None:
            # Format: urn:uuid:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
            # We'll use the UUID part as message ID
            message_id = id_elem.text.replace('urn:uuid:', '') if id_elem.text else ''
        
        # Extract in-reply-to (threading info)
        in_reply_to_elem = entry.find('thr:in-reply-to', self.NS)
        in_reply_to = ''
        if in_reply_to_elem is not None:
            ref_attr = in_reply_to_elem.get('ref', '')
            in_reply_to = ref_attr.replace('urn:uuid:', '') if ref_attr else ''
        
        # Extract content (email body)
        content_elem = entry.find('atom:content', self.NS)
        body = ''
        if content_elem is not None:
            # Content is wrapped in div/pre tags
            div = content_elem.find('{http://www.w3.org/1999/xhtml}div')
            if div is not None:
                pre = div.find('{http://www.w3.org/1999/xhtml}pre')
                if pre is not None:
                    # Get text and decode HTML entities
                    body = ''.join(pre.itertext())
                    body = html.unescape(body)
        
        return {
            'message_id': message_id,
            'subject': subject,
            'from': from_addr,
            'date': date_str,
            'in_reply_to': in_reply_to,
            'references': [in_reply_to] if in_reply_to else [],  # Simplified
            'body': body,
            'raw': ET.tostring(entry, encoding='unicode')[:1000]
        }
