from typing import List, Dict, Set
from collections import defaultdict

class ThreadBuilder:
    """Builds thread structure from emails"""
    
    def __init__(self, emails: List[Dict]):
        """
        Initialize with list of emails
        
        Args:
            emails: List of email dictionaries with message_id, in_reply_to, references
        """
        self.emails = emails
        self.email_map = {e['message_id']: e for e in emails if e.get('message_id')}
    
    def build_threads(self) -> Dict[str, List[Dict]]:
        """
        Build thread structure
        
        Returns:
            Dictionary mapping root_message_id -> list of emails in thread
            
        Algorithm:
        1. For each email, find its root (first email in thread)
        2. Group all emails by their root
        3. Return grouped threads
        """
        print("🧵 Building thread structure...")
        
        threads = defaultdict(list)
        
        for email in self.emails:
            root_id = self._find_thread_root(email)
            threads[root_id].append(email)
        
        print(f"✅ Built {len(threads)} threads from {len(self.emails)} emails")
        return dict(threads)
    
    def _find_thread_root(self, email: Dict) -> str:
        """
        Find the root message of a thread
        
        Args:
            email: Email dictionary
            
        Returns:
            Message ID of the root email
            
        Algorithm:
        1. Check if email has in_reply_to
        2. If yes, follow the chain back to the root
        3. If no, this email IS the root
        4. Use references as backup if in_reply_to is missing
        """
        current_id = email.get('message_id')
        if not current_id:
            return ''
        
        visited = set()  # Prevent infinite loops
        
        # Follow the in_reply_to chain
        while current_id:
            if current_id in visited:
                break  # Circular reference detected
            
            visited.add(current_id)
            
            current_email = self.email_map.get(current_id)
            if not current_email:
                break
            
            # Check if this email replies to something
            parent_id = current_email.get('in_reply_to')
            
            if parent_id and parent_id in self.email_map:
                # Go one level up
                current_id = parent_id
                continue
            
            # Check references as backup
            references = current_email.get('references', [])
            if references and len(references) > 0:
                # First reference is usually the original email
                first_ref = references[0]
                if first_ref in self.email_map:
                    return first_ref
            
            # This is the root!
            return current_id
        
        return current_id or email.get('message_id', '')
    
    def get_thread_metadata(self, thread_emails: List[Dict]) -> Dict:
        """
        Calculate metadata for a thread
        
        Args:
            thread_emails: List of emails in the thread
            
        Returns:
            Dictionary with thread statistics
        """
        if not thread_emails:
            return {}
        
        # Get unique participants
        participants = set()
        for email in thread_emails:
            from_addr = email.get('from', '')
            if from_addr:
                participants.add(from_addr)
        
        # Get date range
        dates = [e.get('date', '') for e in thread_emails if e.get('date')]
        dates.sort()
        
        # Root email
        root_email = thread_emails[0]
        
        return {
            'root_message_id': root_email.get('message_id'),
            'subject': root_email.get('subject'),
            'participant_count': len(participants),
            'email_count': len(thread_emails),
            'first_post': dates[0] if dates else None,
            'last_post': dates[-1] if dates else None,
            'tags': self._extract_tags(root_email.get('subject', ''))
        }
    
    def _extract_tags(self, subject: str) -> List[str]:
        """
        Extract tags from subject line
        
        LKML subjects often have tags like [PATCH], [RFC], [v2], etc.
        Example: "[PATCH v2 net-next] Fix memory leak" -> ['PATCH', 'v2', 'net-next']
        """
        import re
        tags = re.findall(r'\[([^\]]+)\]', subject)
        return tags
