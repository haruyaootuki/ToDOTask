"""
Security utilities for the ToDo application
"""

import time
import hashlib
import re
from collections import defaultdict
from datetime import datetime, timedelta
from flask import request

class SecurityHeaders:
    """Apply security headers to responses"""
    
    @staticmethod
    def apply_headers(response):
        """Apply comprehensive security headers"""
        # XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://cdn.replit.com; "
            "script-src 'self' 'unsafe-inline'; "
            "font-src 'self' https://cdn.replit.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Additional security headers
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Cache control for sensitive pages
        if request.endpoint not in ['static']:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response

class RateLimiter:
    """Simple rate limiter to prevent abuse"""
    
    def __init__(self, max_requests=100, time_window=3600):
        self.max_requests = max_requests  # Maximum requests per time window
        self.time_window = time_window    # Time window in seconds (1 hour)
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip):
        """Check if client is allowed to make a request"""
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove old requests outside the time window
        client_requests[:] = [req_time for req_time in client_requests if now - req_time < self.time_window]
        
        # Check if client has exceeded rate limit
        if len(client_requests) >= self.max_requests:
            return False
        
        # Record this request
        client_requests.append(now)
        return True
    
    def get_remaining_requests(self, client_ip):
        """Get remaining requests for client"""
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove old requests
        client_requests[:] = [req_time for req_time in client_requests if now - req_time < self.time_window]
        
        return max(0, self.max_requests - len(client_requests))

class InputSanitizer:
    """Sanitize and validate user inputs"""
    
    @staticmethod
    def sanitize_text(text):
        """Sanitize text input"""
        if not isinstance(text, str):
            return ""
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Limit length
        text = text[:1000]
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def validate_task_description(description):
        """Validate task description"""
        if not description or not isinstance(description, str):
            return False
        
        # Check length
        if len(description.strip()) < 1 or len(description) > 500:
            return False
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
            r'onmouseover=',
        ]
        
        description_lower = description.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, description_lower):
                return False
        
        return True
    
    @staticmethod
    def generate_csrf_token():
        """Generate a CSRF token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_data(data):
        """Hash data for integrity checking"""
        return hashlib.sha256(str(data).encode()).hexdigest()

class SecurityLogger:
    """Log security events"""
    
    @staticmethod
    def log_suspicious_activity(client_ip, activity_type, details=""):
        """Log suspicious activity"""
        timestamp = datetime.now().isoformat()
        print(f"[SECURITY] {timestamp} - IP: {client_ip} - Type: {activity_type} - Details: {details}")
    
    @staticmethod
    def log_rate_limit_exceeded(client_ip):
        """Log rate limit violations"""
        SecurityLogger.log_suspicious_activity(client_ip, "RATE_LIMIT_EXCEEDED")
    
    @staticmethod
    def log_invalid_input(client_ip, input_type, input_value="[REDACTED]"):
        """Log invalid input attempts"""
        SecurityLogger.log_suspicious_activity(client_ip, "INVALID_INPUT", f"Type: {input_type}")
    
    @staticmethod
    def log_csrf_violation(client_ip):
        """Log CSRF token violations"""
        SecurityLogger.log_suspicious_activity(client_ip, "CSRF_VIOLATION")
