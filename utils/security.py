"""
Security utilities for the PSS RAG system.
Implements input validation, rate limiting, and privacy controls.
"""

import re
import time
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import streamlit as st
from config import Config
from utils.logger import logger

class SecurityManager:
    """Manages security aspects of the RAG system"""
    
    def __init__(self):
        # Rate limiting storage
        self.rate_limit_store: Dict[str, deque] = defaultdict(deque)
        
        # Blocked patterns for input validation
        self.blocked_patterns = [
            r'<script.*?>.*?</script>',  # XSS prevention
            r'javascript:',  # JavaScript injection
            r'data:text/html',  # Data URI attacks
            r'vbscript:',  # VBScript injection
            r'\bUNION\b.*\bSELECT\b',  # SQL injection attempts
            r'\bDROP\b.*\bTABLE\b',  # SQL injection attempts
            r'eval\s*\(',  # Code injection
            r'exec\s*\(',  # Code execution
        ]
        
        # Sensitive data patterns to redact
        self.sensitive_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),  # SSN
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_REDACTED]'),  # Credit card
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),  # Email
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]'),  # Phone number
        ]
    
    def get_client_ip(self) -> str:
        """Get client IP address for rate limiting"""
        # In Streamlit, we use session state as identifier
        if 'client_id' not in st.session_state:
            st.session_state.client_id = hashlib.md5(
                str(time.time()).encode()
            ).hexdigest()[:16]
        return st.session_state.client_id
    
    def check_rate_limit(self, client_id: str) -> Tuple[bool, int]:
        """
        Check if client has exceeded rate limit.
        Returns (allowed, remaining_requests)
        """
        now = time.time()
        minute_ago = now - 60
        
        # Clean old entries
        while (self.rate_limit_store[client_id] and 
               self.rate_limit_store[client_id][0] < minute_ago):
            self.rate_limit_store[client_id].popleft()
        
        current_requests = len(self.rate_limit_store[client_id])
        
        if current_requests >= Config.RATE_LIMIT_PER_MINUTE:
            logger.log_security_event(
                "RATE_LIMIT_EXCEEDED", 
                f"Client {client_id} exceeded rate limit", 
                "WARNING"
            )
            return False, 0
        
        # Add current request
        self.rate_limit_store[client_id].append(now)
        remaining = Config.RATE_LIMIT_PER_MINUTE - current_requests - 1
        
        return True, remaining
    
    def validate_input(self, user_input: str) -> Tuple[bool, str]:
        """
        Validate user input for security threats.
        Returns (is_valid, cleaned_input)
        """
        if not user_input or not user_input.strip():
            return False, "Empty input not allowed"
        
        # Check length
        if len(user_input) > Config.MAX_QUERY_LENGTH:
            logger.log_security_event(
                "INPUT_TOO_LONG", 
                f"Input length: {len(user_input)}", 
                "WARNING"
            )
            return False, f"Input too long. Maximum {Config.MAX_QUERY_LENGTH} characters allowed."
        
        # Check for malicious patterns
        user_input_lower = user_input.lower()
        for pattern in self.blocked_patterns:
            if re.search(pattern, user_input_lower, re.IGNORECASE):
                logger.log_security_event(
                    "MALICIOUS_INPUT_DETECTED", 
                    f"Pattern matched: {pattern}", 
                    "CRITICAL"
                )
                return False, "Input contains potentially malicious content"
        
        # Clean and return
        cleaned_input = self.sanitize_input(user_input)
        return True, cleaned_input
    
    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input"""
        # Remove any HTML tags
        cleaned = re.sub(r'<[^>]+>', '', user_input)
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive information from text"""
        redacted_text = text
        
        for pattern, replacement in self.sensitive_patterns:
            redacted_text = re.sub(pattern, replacement, redacted_text)
        
        return redacted_text
    
    def log_user_interaction(self, query: str, response_preview: str):
        """Log user interactions for audit purposes (with privacy protection)"""
        # Hash the query for privacy
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        
        # Create safe preview (first 100 chars, redacted)
        safe_preview = self.redact_sensitive_data(response_preview[:100])
        
        logger.info(
            f"User interaction logged - Query hash: {query_hash}, "
            f"Response preview: {safe_preview}..."
        )
    
    def check_content_policy(self, text: str) -> Tuple[bool, str]:
        """Check if content violates usage policies"""
        
        # Define prohibited content categories
        prohibited_patterns = [
            (r'\b(hack|exploit|vulnerability)\b', "Security-related content"),
            (r'\b(illegal|criminal|fraud)\b', "Illegal activity content"),
            (r'\b(violence|harmful|dangerous)\b', "Harmful content"),
        ]
        
        text_lower = text.lower()
        
        for pattern, category in prohibited_patterns:
            if re.search(pattern, text_lower):
                logger.log_security_event(
                    "CONTENT_POLICY_VIOLATION",
                    f"Category: {category}",
                    "WARNING"
                )
                return False, f"Content violates policy: {category}"
        
        return True, "Content approved"
    
    def get_session_info(self) -> Dict:
        """Get current session security information"""
        client_id = self.get_client_ip()
        allowed, remaining = self.check_rate_limit(client_id)
        
        return {
            "client_id": client_id,
            "rate_limit_remaining": remaining,
            "session_start": st.session_state.get('session_start', datetime.now()),
            "requests_made": len(self.rate_limit_store[client_id])
        }

# Global security manager instance
security_manager = SecurityManager() 