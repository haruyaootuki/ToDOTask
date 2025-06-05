"""
Input validation utilities
"""

import re
import html
from typing import Any, Union

# Define a constant for control characters pattern
CONTROL_CHARS_PATTERN = r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'

class TaskValidator:
    """Validate task-related inputs"""
    
    @staticmethod
    def validate_description(description: Any) -> bool:
        """Validate task description"""
        if not isinstance(description, str):
            return False
        
        # Check length
        if len(description.strip()) < 1 or len(description) > 500:
            return False
        
        # Check for null bytes and control characters
        if re.search(CONTROL_CHARS_PATTERN, description):
            return False
        
        # Check for potentially dangerous HTML/JS patterns
        dangerous_patterns = [
            r'<script[^>]*?>.*?</script>',
            r'<iframe[^>]*?>.*?</iframe>',
            r'<object[^>]*?>.*?</object>',
            r'<embed[^>]*?>.*?</embed>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'on\w+\s*=',  # Event handlers like onclick, onload, etc.
        ]
        
        description_lower = description.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, description_lower):
                return False
        
        return True
    
    @staticmethod
    def validate_task_id(task_id: Any) -> bool:
        """Validate task ID"""
        if not isinstance(task_id, (int, str)):
            return False
        
        try:
            task_id_int = int(task_id)
            result = 1 <= task_id_int <= 999999
            return result
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_filter_type(filter_type: Any) -> bool:
        """Validate filter type"""
        return isinstance(filter_type, str) and filter_type in ['all', 'active', 'completed']
    
    @staticmethod
    def sanitize_description(description: str) -> str:
        """Sanitize task description"""
        if not isinstance(description, str):
            return ""
        
        # Remove null bytes and control characters
        description = re.sub(CONTROL_CHARS_PATTERN, '', description)
        
        # Strip whitespace
        description = description.strip()
        
        # Escape HTML to prevent XSS
        description = html.escape(description)
        
        # Limit length
        description = description[:500]
        
        return description

class SecurityValidator:
    """General security validation utilities"""
    
    @staticmethod
    def is_safe_string(value: Any, max_length: int = 1000) -> bool:
        """Check if string is safe for processing"""
        if not isinstance(value, str):
            return False
        
        if len(value) > max_length:
            return False
        
        # Check for null bytes and dangerous control characters
        if re.search(CONTROL_CHARS_PATTERN, value):
            return False
        
        return True
    
    @staticmethod
    def validate_csrf_token(token: Any) -> bool:
        """Validate CSRF token format"""
        if not isinstance(token, str):
            return False
        
        # Check token format (base64url characters)
        if not re.match(r'^[A-Za-z0-9_-]+$', token):
            return False
        
        # Check reasonable length
        if len(token) < 16 or len(token) > 128:
            return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename (if needed for future features)"""
        if not isinstance(filename, str):
            return "unknown"
        
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Limit length
        filename = filename[:255]
        
        return filename or "unknown"

class RequestValidator:
    """Validate HTTP requests"""
    
    @staticmethod
    def validate_content_type(request, expected_types: list) -> bool:
        """Validate request content type"""
        content_type = request.content_type or ""
        return any(expected in content_type for expected in expected_types)
    
    @staticmethod
    def validate_request_size(request, max_size: int = 1024 * 1024) -> bool:
        """Validate request size"""
        content_length = request.content_length
        if content_length is None:
            return True  # No content length header
        
        return content_length <= max_size
    
    @staticmethod
    def get_client_ip(request) -> str:
        """Get client IP address safely"""
        # Check for forwarded headers (in order of preference)
        forwarded_headers = [
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'HTTP_X_FORWARDED',
            'HTTP_FORWARDED_FOR',
            'HTTP_FORWARDED'
        ]
        
        for header in forwarded_headers:
            ip = request.environ.get(header)
            if ip:
                # Take the first IP if multiple are present
                ip = ip.split(',')[0].strip()
                if TaskValidator.validate_ip(ip):
                    return ip
        
        # Fallback to remote_addr
        return request.environ.get('REMOTE_ADDR', 'unknown')
    
    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address format"""
        if not isinstance(ip, str):
            return False
        
        # Simple IPv4 validation
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
            return True
        except ValueError:
            return False
