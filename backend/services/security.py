"""
Production security utilities and configuration
"""
import secrets
import os
from typing import List
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
from collections import defaultdict

class SecurityManager:
    """Enhanced security manager for production"""
    
    def __init__(self):
        self.rate_limit_storage = defaultdict(list)
        self.security = HTTPBearer()
    
    @staticmethod
    def generate_jwt_secret() -> str:
        """Generate a cryptographically secure JWT secret"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return f"ak_{secrets.token_urlsafe(32)}"
    
    def validate_environment(self) -> List[str]:
        """Validate production environment variables"""
        errors = []
        warnings = []
        
        # Critical environment variables
        required_vars = [
            "JWT_SECRET",
            "MONGODB_URI", 
            "OPENAI_KEY",
            "BASE_URL"
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Security validations
        jwt_secret = os.getenv("JWT_SECRET", "")
        if jwt_secret == "test-jwt-secret" or len(jwt_secret) < 32:
            errors.append("JWT_SECRET is insecure - must be at least 32 characters")
        
        openai_key = os.getenv("OPENAI_KEY", "")
        if openai_key.startswith("sk-test") or not openai_key.startswith("sk-"):
            warnings.append("OPENAI_KEY appears to be invalid or test key")
        
        base_url = os.getenv("BASE_URL", "")
        if base_url.startswith("http://") and os.getenv("APP_ENV") == "production":
            warnings.append("BASE_URL should use HTTPS in production")
        
        # Print results
        if errors:
            print("🚨 SECURITY ERRORS:")
            for error in errors:
                print(f"   ❌ {error}")
        
        if warnings:
            print("⚠️ SECURITY WARNINGS:")
            for warning in warnings:
                print(f"   ⚠️ {warning}")
        
        if not errors and not warnings:
            print("✅ Security validation passed")
        
        return errors
    
    def rate_limit_check(self, request: Request, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Simple in-memory rate limiting based on session"""
        # Get client identifier from session or generate one
        client_id = "anonymous"
        if hasattr(request.state, 'user') and request.state.user:
            client_id = f"user_{request.state.user.id}"
        elif hasattr(request, 'session') and request.session.get('session_id'):
            client_id = f"session_{request.session['session_id']}"
        
        current_time = time.time()
        
        # Clean old entries
        cutoff_time = current_time - window_seconds
        self.rate_limit_storage[client_id] = [
            timestamp for timestamp in self.rate_limit_storage[client_id] 
            if timestamp > cutoff_time
        ]
        
        # Check rate limit
        if len(self.rate_limit_storage[client_id]) >= max_requests:
            return False
        
        # Add current request
        self.rate_limit_storage[client_id].append(current_time)
        return True

# Global security manager
security_manager = SecurityManager()

def validate_production_security():
    """Validate security configuration on startup"""
    return security_manager.validate_environment()

def check_rate_limit(request: Request):
    """Rate limiting dependency"""
    max_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    window = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
    
    if not security_manager.rate_limit_check(request, max_requests, window):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )

def get_security_headers():
    """Get security headers for responses"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }