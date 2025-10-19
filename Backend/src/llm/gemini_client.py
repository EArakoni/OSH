"""
Google Gemini API client for LKML email summarization
Improved version with rate limiting, retry logic, caching, and better error handling
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    # Model configurations (updated to stable versions)
    MODELS = {
        'flash': 'gemini-2.5-flash',           # Fast, cheap, good for most tasks
        'flash-8b': 'gemini-2.5-flash-8b',     # Even faster, cheaper
        'pro': 'gemini-2.5-pro',               # Slower, better quality
        'flash-exp': 'gemini-2.5-flash-exp'    # Experimental 2.0 (if available)
    }
    
    # Token limits (leave buffer for response)
    TOKEN_LIMITS = {
        'flash': 900000,      # 1M limit, use 900k for safety
        'flash-8b': 900000,   # 1M limit
        'pro': 1900000,       # 2M limit, use 1.9M for safety
        'flash-exp': 900000   # 1M limit
    }
    
    # Rate limiting (requests per minute)
    RATE_LIMITS = {
        'flash': 15,          # 15 requests per minute (free tier)
        'flash-8b': 15,
        'pro': 2,             # Conservative for pro
        'flash-exp': 15
    }
    
    def __init__(self, api_key: Optional[str] = None, model: str = 'flash', 
                 enable_cache: bool = True, cache_dir: str = 'cache/gemini'):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google AI API key (or set GEMINI_API_KEY env var)
            model: 'flash', 'flash-8b', 'pro', or 'flash-exp'
            enable_cache: Enable response caching to save API calls
            cache_dir: Directory to store cached responses
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY environment "
                "variable or pass api_key parameter."
            )
        
        genai.configure(api_key=self.api_key)
        
        self.model_type = model
        self.model_name = self.MODELS.get(model, self.MODELS['flash'])
        self.model = genai.GenerativeModel(self.model_name)
        
        # Generation config for consistent outputs
        self.generation_config = {
            'temperature': 0.3,  # Lower for factual summaries
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 8192,
        }
        
        # Safety settings - disable for technical/code content
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            },
        ]
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()
        self.rate_limit = self.RATE_LIMITS.get(model, 15)
        
        # Caching
        self.enable_cache = enable_cache
        self.cache_dir = Path(cache_dir)
        if enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics
        self.metrics = {
            'api_calls': 0,
            'cache_hits': 0,
            'errors': 0,
            'total_tokens_estimate': 0
        }
        
        print(f"✅ Gemini client initialized")
        print(f"   Model: {self.model_name}")
        print(f"   Cache: {'enabled' if enable_cache else 'disabled'}")
        print(f"   Rate limit: {self.rate_limit} requests/minute")
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        
        # Reset counter if we're in a new minute window
        if current_time - self.request_window_start >= 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        # If we've hit the rate limit, wait
        if self.request_count >= self.rate_limit:
            wait_time = 60 - (current_time - self.request_window_start)
            if wait_time > 0:
                print(f"⏳ Rate limit reached, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                self.request_count = 0
                self.request_window_start = time.time()
        
        self.request_count += 1
    
    def _get_cache_key(self, content: str, summary_type: str) -> str:
        """Generate cache key from content"""
        hash_input = f"{summary_type}:{content}:{self.model_name}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Retrieve from cache if available"""
        if not self.enable_cache:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.metrics['cache_hits'] += 1
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Cache read error: {e}")
                return None
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save response to cache"""
        if not self.enable_cache:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Cache write error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError,
            Exception  # Gemini API errors
        ))
    )
    def _generate_content_with_retry(self, prompt: str) -> Any:
        """
        Generate content with automatic retry on failures
        
        Uses exponential backoff: 2s, 4s, 8s between retries
        """
        self._rate_limit()
        self.metrics['api_calls'] += 1
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Estimate token usage (rough: 4 chars per token)
            estimated_tokens = (len(prompt) + len(response.text)) // 4
            self.metrics['total_tokens_estimate'] += estimated_tokens
            
            return response
            
        except Exception as e:
            self.metrics['errors'] += 1
            error_str = str(e).lower()
            
            # Classify error types
            if 'quota' in error_str or 'rate limit' in error_str:
                print(f"⚠️  API quota/rate limit exceeded")
                raise
            elif 'safety' in error_str or 'blocked' in error_str:
                print(f"⚠️  Content blocked by safety filters")
                raise
            else:
                print(f"⚠️  API error: {e}")
                raise
    
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
            print(f"❌ Error listing models: {e}")
            return []
    
    def summarize_email(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize a single email (typically a thread root)
        
        Args:
            email: Email dictionary with subject, from, body, etc.
            
        Returns:
            Dictionary with summary data
        """
        # Check cache first
        cache_key = self._get_cache_key(
            email.get('body', '') + email.get('subject', ''),
            'email'
        )
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        prompt = self._build_email_prompt(email)
        
        try:
            response = self._generate_content_with_retry(prompt)
            
            # Parse JSON response
            summary_data = self._parse_json_response(response.text)
            
            result = {
                'email_id': email.get('message_id'),
                'summary_type': 'email',
                'tldr': summary_data.get('tldr', ''),
                'key_points': summary_data.get('key_points', []),
                'email_type': summary_data.get('email_type', 'discussion'),
                'patch_version': summary_data.get('patch_version'),
                'subsystems': summary_data.get('subsystems', []),
                'importance': summary_data.get('importance', 'medium'),
                'is_security_related': summary_data.get('is_security_related', False),
                'llm_model': self.model_name,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            
            return result
            
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
        # Check cache
        thread_key = ''.join([e.get('message_id', '') for e in thread_emails])
        cache_key = self._get_cache_key(thread_key, 'thread')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Smart truncation to fit token limits
        thread_emails = self._smart_truncate_thread(thread_emails)
        
        prompt = self._build_thread_prompt(thread_emails, thread_meta)
        
        try:
            response = self._generate_content_with_retry(prompt)
            
            summary_data = self._parse_json_response(response.text)
            
            result = {
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
                'thread_type': summary_data.get('thread_type', 'discussion'),
                'llm_model': self.model_name,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            
            return result
            
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
        # Check cache
        cache_key = self._get_cache_key(f"{date}:{len(threads_data)}", 'digest')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        prompt = self._build_digest_prompt(threads_data, date)
        
        try:
            response = self._generate_content_with_retry(prompt)
            
            digest_data = self._parse_json_response(response.text)
            
            result = {
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
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"❌ Error generating digest: {e}")
            return self._error_summary('daily', str(e))
    
    def _smart_truncate_thread(self, thread_emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Intelligently truncate thread to fit token limits
        Keep: root email, patches, important replies, and latest emails
        """
        if len(thread_emails) <= 10:
            return thread_emails
        
        # Always keep root (first email)
        keep = [thread_emails[0]]
        
        # Add emails with patches (identified by subject)
        patch_emails = []
        for email in thread_emails[1:-3]:
            subject = email.get('subject', '').upper()
            if '[PATCH' in subject or '[RFC' in subject:
                patch_emails.append(email)
        
        # Keep up to 3 patch emails
        keep.extend(patch_emails[:3])
        
        # Always keep last 3 emails
        keep.extend(thread_emails[-3:])
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for email in keep:
            msg_id = email.get('message_id')
            if msg_id not in seen:
                seen.add(msg_id)
                result.append(email)
        
        print(f"  📉 Truncated thread from {len(thread_emails)} to {len(result)} emails")
        return result
    
    def _build_email_prompt(self, email: Dict[str, Any]) -> str:
        """Build LKML-specific prompt for email summarization"""
        subject = email.get('subject', 'No subject')
        sender = email.get('from', 'Unknown')
        body = email.get('body', '')[:5000]  # Limit body length
        
        return f"""You are analyzing a Linux Kernel Mailing List (LKML) email.

CONTEXT: LKML is where Linux kernel developers discuss patches, bugs, and features.
Common patterns:
- [PATCH] = code change proposal
- [RFC] = request for comments (early discussion)
- [v2], [v3], etc. = patch revision number
- Subsystem tags: [net], [mm], [fs], [drivers], etc.
- Security-related emails often have CVE numbers or mention "security", "vulnerability"

EMAIL DETAILS:
Subject: {subject}
From: {sender}

BODY:
{body}

TASK: Provide JSON with this EXACT structure:
{{
    "tldr": "One sentence summary (max 150 chars)",
    "email_type": "patch|rfc|bug|discussion|announcement|security",
    "patch_version": "v2" or null (extract from subject like [PATCH v2]),
    "subsystems": ["networking", "memory-management"],  # From subject tags or content
    "importance": "critical|high|medium|low",
    "is_security_related": true|false,
    "key_points": ["point 1", "point 2", "point 3"]
}}

IMPORTANCE GUIDE:
- critical: security issues, kernel panics, data corruption
- high: major features, widespread bugs, API changes
- medium: normal patches, improvements
- low: typo fixes, minor cleanups

Return ONLY valid JSON. No markdown, no code blocks, no explanations."""
    
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

TASK: Provide JSON with this EXACT structure:
{{
    "tldr": "One sentence summary of entire thread (max 200 chars)",
    "discussion_summary": "2-3 paragraph narrative of the discussion",
    "key_points": ["major point 1", "major point 2", "major point 3"],
    "resolution": "What was decided/concluded (or 'ongoing' if unresolved)",
    "action_items": ["action 1", "action 2"],
    "subsystems": ["affected kernel subsystems"],
    "key_contributors": ["names of main participants"],
    "importance": "critical|high|medium|low",
    "thread_type": "patch_review|bug_fix|feature_discussion|rfc|security|bikeshedding"
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

TASK: Provide JSON with this EXACT structure:
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
            'tldr': f'Error generating summary: {error[:100]}',
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
        
        # Pricing as of October 2025 (check official docs for updates)
        if 'flash' in self.model_name:
            # Flash models: $0.075 per 1M input, $0.30 per 1M output
            cost = (input_tokens / 1_000_000 * 0.075 + 
                   output_tokens / 1_000_000 * 0.30)
        elif 'pro' in self.model_name:
            # Pro models: $1.25 per 1M input, $5.00 per 1M output
            cost = (input_tokens / 1_000_000 * 1.25 + 
                   output_tokens / 1_000_000 * 5.00)
        else:
            cost = 0.0
        
        return cost
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get usage metrics"""
        return {
            **self.metrics,
            'cache_hit_rate': (
                self.metrics['cache_hits'] / 
                (self.metrics['api_calls'] + self.metrics['cache_hits'])
                if (self.metrics['api_calls'] + self.metrics['cache_hits']) > 0
                else 0
            ),
            'estimated_cost': self.estimate_cost(
                self.metrics['total_tokens_estimate'] * 2,  # Rough input estimate
                self.metrics['total_tokens_estimate']        # Rough output estimate
            )
        }
    
    def print_metrics(self):
        """Print usage statistics"""
        metrics = self.get_metrics()
        print("\n" + "="*60)
        print("📊 Gemini API Usage Metrics")
        print("="*60)
        print(f"  API calls: {metrics['api_calls']}")
        print(f"  Cache hits: {metrics['cache_hits']}")
        print(f"  Cache hit rate: {metrics['cache_hit_rate']:.1%}")
        print(f"  Errors: {metrics['errors']}")
        print(f"  Estimated tokens: {metrics['total_tokens_estimate']:,}")
        print(f"  Estimated cost: ${metrics['estimated_cost']:.4f}")
        print("="*60)
