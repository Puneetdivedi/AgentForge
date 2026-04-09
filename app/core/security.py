"""Security utilities for prompt injection protection and input validation"""
import re
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Validates and sanitizes user inputs"""
    
    # Patterns for common prompt injection attempts
    INJECTION_PATTERNS = [
        r"ignore previous instructions",
        r"forget everything",
        r"system prompt",
        r"you are now",
        r"act as",
        r"ignore all previous",
        r"override",
        r"bypass",
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r"('\s*(OR|AND)\s*')",
        r"(;\s*DROP\s+)",
        r"(UNION\s+SELECT)",
        r"(INSERT\s+INTO)",
        r"(DELETE\s+FROM)",
        r"(UPDATE\s+)",
    ]
    
    @staticmethod
    def validate_prompt_injection(text: str) -> bool:
        """
        Detect potential prompt injection
        
        Args:
            text: Input text to validate
            
        Returns:
            True if suspicious pattern detected
        """
        text_lower = text.lower()
        for pattern in SecurityValidator.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Potential prompt injection detected: {pattern}")
                return True
        return False
    
    @staticmethod
    def validate_sql_injection(query: str) -> bool:
        """
        Detect potential SQL injection
        
        Args:
            query: SQL query to validate
            
        Returns:
            True if suspicious pattern detected
        """
        query_upper = query.upper()
        for pattern in SecurityValidator.SQL_PATTERNS:
            if re.search(pattern, query_upper):
                logger.warning(f"Potential SQL injection detected: {pattern}")
                return True
        return False
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 5000) -> str:
        """
        Sanitize user input
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        # Truncate if too long
        if len(text) > max_length:
            logger.warning(f"Input truncated from {len(text)} to {max_length} characters")
            text = text[:max_length]
        
        # Remove null bytes
        text = text.replace("\x00", "")
        
        return text.strip()


class OutputFilter:
    """Filters and sanitizes model outputs"""
    
    @staticmethod
    def filter_sensitive_data(text: str) -> str:
        """
        Filter sensitive data from output
        
        Args:
            text: Text to filter
            
        Returns:
            Filtered text
        """
        # Remove email addresses
        text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)
        
        # Remove phone numbers
        text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", text)
        
        # Remove API keys (simple pattern)
        text = re.sub(r"(api[_-]?key|secret|token)[\s]*[:=][\s]*[^\s]+", "[REDACTED]", text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def filter_profanity(text: str) -> str:
        """
        Basic profanity filtering
        
        Args:
            text: Text to filter
            
        Returns:
            Filtered text
        """
        # This is a placeholder - implement with a proper profanity library
        # Example: from better_profanity import profanity
        return text
