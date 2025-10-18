"""
Google Gemini API client for LKML email summarization
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai

class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    # Model configurations
    MODELS = {
        'flash': 'models/gemini-2.5-flash-preview-05-20',
        'pro': 'models/gemini-2.5-pro-preview-03-25'
    }
    
    # Token limits (leave buffer for response)
    TOKEN_LIMITS = {
        'flash': 900000,  # 1M limit, use 900k for safety
        'pro': 1900000    # 2M limit, use 1.9M for safety
    }
    
    def __init__(self, api_key: Optional[str] = None, model: str = 'flash'):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google AI API key (or set GEMINI_API_KEY env var)
            model: 'flash' or 'pro'
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY environment "
                "variable or pass api_key parameter."
            )
        
        genai.configure(api_key=self.api_key)
        
        self.model_name = self.MODELS.get(model, self.MODELS['flash'])
        self.model = genai.GenerativeModel(self.model_name)
        
        # Generation config for consistent outputs
        self.generation_config = {
            'temperature': 0.3,  # Lower for factual summaries
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 2048,
        }
        
        print(f"✅ Gemini client initialized with model: {self.model_name}")
    
    @staticmethod
    def list_available_models():
        """List all available Gemini models"""
        try:
            models = genai.list_models()
            print("Available Gemini models:")
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    print(f"  - {model.name}")
            return [m.name for m in models]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    def summarize_email(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize a single email (typically a thread root)
        
        Args:
            email: Email dictionary with subject, from, body, etc.
            
        Returns:
            Dictionary with summary data
        """
        prompt = self._build_email_prompt(email)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse JSON response
            summary_data = self._parse_json_response(response.text)
            
            return {
                'email_id': email.get('message_id'),
                'summary_type': 'email',
                'tldr': summary_data.get('tldr', ''),
                'key_points': summary_data.get('key_points', []),
                'email_type': summary_data.get('email_type', 'discussion'),
                'subsystems': summary_data.get('subsystems', []),
                'importance': summary_data.get('importance', 'medium'),
                'llm_model': self.model_name,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error summarizing email: {e}")
            return self._error_summary('email', str(e))
    
    def summarize_thread(self, thread_emails: List[Dict[str, Any]], 
                        thread_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize an entire email thread
        
        Args:
            thread_emails: List of emails in thread (chronological order)
            thread_meta: Thread metadata (subject, participant_count, etc.)
            
        Returns:
            Dictionary with thread summary
        """
        # Check if thread is too large
        estimated_tokens = sum(len(e.get('body', '')) for e in thread_emails) // 4
        
        if estimated_tokens > self.TOKEN_LIMITS[self.model_name.split('-')[-1]]:
            # Truncate thread - keep first 3 and last 3 emails
            if len(thread_emails) > 6:
                thread_emails = thread_emails[:3] + thread_emails[-3:]
        
        prompt = self._build_thread_prompt(thread_emails, thread_meta)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            summary_data = self._parse_json_response(response.text)
            
            return {
                'summary_type': 'thread',
                'subject': thread_meta.get('subject'),
                'tldr': summary_data.get('tldr', ''),
                'key_points': summary_data.get('key_points', []),
                'discussion_summary': summary_data.get('discussion_summary', ''),
                'resolution': summary_data.get('resolution', ''),
                'action_items': summary_data.get('action_items', []),
                'subsystems': summary_data.get('subsystems', []),
                'key_contributors': summary_data.get('key_contributors', []),
                'importance': summary_data.get('importance', 'medium'),
                'llm_model': self.model_name,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error summarizing thread: {e}")
            return self._error_summary('thread', str(e))
    
    def generate_daily_digest(self, threads_data: List[Dict[str, Any]], 
                             date: str) -> Dict[str, Any]:
        """
        Generate a daily digest of LKML activity
        
        Args:
            threads_data: List of thread summaries for the day
            date: Date string (YYYY-MM-DD)
            
        Returns:
            Dictionary with daily digest
        """
        prompt = self._build_digest_prompt(threads_data, date)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            digest_data = self._parse_json_response(response.text)
            
            return {
                'summary_type': 'daily',
                'date': date,
                'tldr': digest_data.get('tldr', ''),
                'highlights': digest_data.get('highlights', []),
                'by_subsystem': digest_data.get('by_subsystem', {}),
                'hot_topics': digest_data.get('hot_topics', []),
                'critical_items': digest_data.get('critical_items', []),
                'statistics': digest_data.get('statistics', {}),
                'llm_model': self.model_name,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error generating digest: {e}")
            return self._error_summary('daily', str(e))
    
    def _build_email_prompt(self, email: Dict[str, Any]) -> str:
        """Build prompt for email summarization"""
        subject = email.get('subject', 'No subject')
        sender = email.get('from', 'Unknown')
        body = email.get('body', '')[:5000]  # Limit body length
        
        return f"""Analyze this Linux Kernel Mailing List (LKML) email and provide a structured summary.

EMAIL DETAILS:
Subject: {subject}
From: {sender}

BODY:
{body}

TASK: Provide a JSON response with the following structure:
{{
    "tldr": "One sentence summary (max 150 chars)",
    "email_type": "patch|rfc|bug|discussion|announcement",
    "key_points": ["point 1", "point 2", "point 3"],
    "subsystems": ["subsystem names mentioned, e.g., networking, fs, mm"],
    "importance": "critical|high|medium|low",
    "technical_details": {{
        "files_modified": ["list if patch"],
        "bug_severity": "critical|high|medium|low if bug report",
        "proposed_changes": "brief description if patch/RFC"
    }}
}}

GUIDELINES:
- Be concise and technical
- Extract kernel subsystems from subject tags and content
- Classify importance based on: security issues, major features, widespread impact
- For patches: identify what's being changed and why
- For bugs: identify severity and affected components
- Return ONLY valid JSON, no markdown formatting"""
    
    def _build_thread_prompt(self, thread_emails: List[Dict[str, Any]], 
                            thread_meta: Dict[str, Any]) -> str:
        """Build prompt for thread summarization"""
        subject = thread_meta.get('subject', 'No subject')
        email_count = len(thread_emails)
        
        # Build thread conversation
        conversation = []
        for i, email in enumerate(thread_emails, 1):
            sender = email.get('from', 'Unknown').split('<')[0].strip()
            body_preview = email.get('body', '')[:1000]
            conversation.append(f"[Email {i}] {sender}:\n{body_preview}\n")
        
        thread_text = "\n---\n".join(conversation)
        
        return f"""Analyze this Linux Kernel Mailing List (LKML) thread and provide a comprehensive summary.

THREAD SUBJECT: {subject}
EMAILS IN THREAD: {email_count}

CONVERSATION:
{thread_text}

TASK: Provide a JSON response with the following structure:
{{
    "tldr": "One sentence summary of entire thread (max 200 chars)",
    "discussion_summary": "2-3 paragraph narrative of the discussion",
    "key_points": ["major point 1", "major point 2", "major point 3"],
    "resolution": "What was decided/concluded (or 'ongoing' if unresolved)",
    "action_items": ["action 1", "action 2"],
    "subsystems": ["affected kernel subsystems"],
    "key_contributors": ["names of main participants"],
    "importance": "critical|high|medium|low",
    "thread_type": "patch_review|bug_fix|feature_discussion|rfc|bikeshedding"
}}

GUIDELINES:
- Focus on technical substance and outcomes
- Identify consensus vs ongoing debate
- Note if patches were accepted/rejected/need_revision
- Highlight any security concerns or breaking changes
- Extract action items and next steps
- Return ONLY valid JSON, no markdown formatting"""
    
    def _build_digest_prompt(self, threads_data: List[Dict[str, Any]], 
                            date: str) -> str:
        """Build prompt for daily digest"""
        # Summarize threads
        thread_summaries = []
        for i, thread in enumerate(threads_data[:20], 1):  # Limit to top 20
            thread_summaries.append(
                f"{i}. [{thread.get('importance', 'medium')}] "
                f"{thread.get('subject', 'No subject')}\n"
                f"   TL;DR: {thread.get('tldr', 'N/A')}\n"
                f"   Subsystems: {', '.join(thread.get('subsystems', []))}"
            )
        
        threads_text = "\n\n".join(thread_summaries)
        
        return f"""Generate a daily digest for the Linux Kernel Mailing List (LKML) for {date}.

THREADS TODAY ({len(threads_data)} total):
{threads_text}

TASK: Provide a JSON response with the following structure:
{{
    "tldr": "Executive summary of the day's activity (2-3 sentences)",
    "highlights": [
        "Most important development 1",
        "Most important development 2",
        "Most important development 3"
    ],
    "by_subsystem": {{
        "networking": ["brief updates"],
        "filesystem": ["brief updates"],
        "memory management": ["brief updates"]
    }},
    "hot_topics": ["controversial or high-activity topics"],
    "critical_items": ["security issues, breaking changes, urgent bugs"],
    "statistics": {{
        "total_threads": {len(threads_data)},
        "critical_threads": 0,
        "high_importance": 0,
        "patches_submitted": 0
    }}
}}

GUIDELINES:
- Prioritize security issues, breaking changes, and major features
- Group related discussions by subsystem
- Highlight controversies or significant debates
- Make it useful for kernel maintainers to quickly scan
- Return ONLY valid JSON, no markdown formatting"""
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON from Gemini response, handling markdown code blocks"""
        try:
            # Remove markdown code blocks if present
            cleaned = response_text.strip()
            if cleaned.startswith('```'):
                # Remove ```json and ``` markers
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1])
            
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            print(f"Response was: {response_text[:500]}")
            return {}
    
    def _error_summary(self, summary_type: str, error: str) -> Dict:
        """Return error summary structure"""
        return {
            'summary_type': summary_type,
            'error': error,
            'tldr': f'Error generating summary: {error}',
            'llm_model': self.model_name,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def estimate_cost(self, input_chars: int, output_chars: int = 1000) -> float:
        """
        Estimate API cost for a request
        
        Args:
            input_chars: Number of input characters
            output_chars: Expected output characters
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimate: 4 chars per token
        input_tokens = input_chars / 4
        output_tokens = output_chars / 4
        
        if 'flash' in self.model_name:
            # $0.075 per 1M input, $0.30 per 1M output
            cost = (input_tokens / 1_000_000 * 0.075 + 
                   output_tokens / 1_000_000 * 0.30)
        else:  # pro
            # $1.25 per 1M input, $5.00 per 1M output
            cost = (input_tokens / 1_000_000 * 1.25 + 
                   output_tokens / 1_000_000 * 5.00)
        
        return cost
