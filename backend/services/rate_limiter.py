"""
Rate limiting service to prevent abuse of email and API endpoints
"""
import time
from collections import defaultdict
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import hashlib

@dataclass
class RateLimitRule:
    """Configuration for rate limiting rules"""
    max_requests: int
    window_seconds: int
    burst_limit: Optional[int] = None  # Allow short bursts
    cooldown_seconds: Optional[int] = None  # Cooldown after limit exceeded

@dataclass
class RateLimitRecord:
    """Track rate limit attempts"""
    requests: List[float] = field(default_factory=list)
    blocked_until: Optional[float] = None
    total_blocked: int = 0

class EmailRateLimiter:
    """Rate limiter specifically for email operations"""
    
    def __init__(self):
        # Storage for rate limit records: {key: RateLimitRecord}
        self._records: Dict[str, RateLimitRecord] = defaultdict(RateLimitRecord)
        
        # Email-specific rate limit rules
        self.rules = {
            # Per email address limits
            'email_per_address': RateLimitRule(
                max_requests=5,      # 5 emails per hour per address
                window_seconds=3600,
                burst_limit=2,       # Allow 2 quick emails
                cooldown_seconds=300 # 5 minute cooldown after limit
            ),
            
            # Per IP address limits (for form submissions triggering emails)
            'email_per_ip': RateLimitRule(
                max_requests=20,     # 20 emails per hour per IP
                window_seconds=3600,
                cooldown_seconds=600 # 10 minute cooldown
            ),
            
            # Global email rate limit
            'email_global': RateLimitRule(
                max_requests=100,    # 100 emails per hour globally
                window_seconds=3600,
                cooldown_seconds=1800 # 30 minute cooldown
            ),
            
            # Per user limits
            'email_per_user': RateLimitRule(
                max_requests=10,     # 10 emails per hour per user
                window_seconds=3600,
                cooldown_seconds=300
            )
        }
    
    def _generate_key(self, rule_name: str, identifier: str) -> str:
        """Generate consistent key for rate limiting"""
        # Hash identifier for privacy and consistent length
        id_hash = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return f"email_rate:{rule_name}:{id_hash}"
    
    def _cleanup_old_records(self, record: RateLimitRecord, window_seconds: int) -> None:
        """Remove old request timestamps outside the window"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        record.requests = [req_time for req_time in record.requests if req_time > cutoff_time]
    
    def check_rate_limit(self, email_address: str, user_id: Optional[str] = None, 
                        ip_address: Optional[str] = None) -> tuple[bool, str]:
        """
        Check if email sending is allowed based on rate limits
        Returns (allowed: bool, reason: str)
        """
        current_time = time.time()
        
        # Check each applicable rate limit
        checks = [
            ('email_per_address', email_address),
            ('email_global', 'global')
        ]
        
        if user_id:
            checks.append(('email_per_user', user_id))
        
        if ip_address:
            checks.append(('email_per_ip', ip_address))
        
        for rule_name, identifier in checks:
            rule = self.rules[rule_name]
            key = self._generate_key(rule_name, identifier)
            record = self._records[key]
            
            # Check if currently in cooldown
            if record.blocked_until and current_time < record.blocked_until:
                remaining = int(record.blocked_until - current_time)
                return False, f"Rate limit exceeded for {rule_name}. Try again in {remaining} seconds."
            
            # Clear expired block
            if record.blocked_until and current_time >= record.blocked_until:
                record.blocked_until = None
            
            # Clean up old requests
            self._cleanup_old_records(record, rule.window_seconds)
            
            # Check rate limit
            if len(record.requests) >= rule.max_requests:
                # Apply cooldown if configured
                if rule.cooldown_seconds:
                    record.blocked_until = current_time + rule.cooldown_seconds
                    record.total_blocked += 1
                
                return False, f"Rate limit exceeded for {rule_name}. Maximum {rule.max_requests} requests per {rule.window_seconds} seconds."
        
        return True, "Rate limit check passed"
    
    def record_email_sent(self, email_address: str, user_id: Optional[str] = None, 
                         ip_address: Optional[str] = None) -> None:
        """Record that an email was sent for rate limiting purposes"""
        current_time = time.time()
        
        # Record for each applicable rate limit
        identifiers = [
            ('email_per_address', email_address),
            ('email_global', 'global')
        ]
        
        if user_id:
            identifiers.append(('email_per_user', user_id))
        
        if ip_address:
            identifiers.append(('email_per_ip', ip_address))
        
        for rule_name, identifier in identifiers:
            key = self._generate_key(rule_name, identifier)
            record = self._records[key]
            record.requests.append(current_time)
    
    def get_rate_limit_status(self, email_address: str, user_id: Optional[str] = None) -> Dict:
        """Get current rate limit status for monitoring"""
        current_time = time.time()
        status = {}
        
        checks = [('email_per_address', email_address)]
        if user_id:
            checks.append(('email_per_user', user_id))
        
        for rule_name, identifier in checks:
            rule = self.rules[rule_name]
            key = self._generate_key(rule_name, identifier)
            record = self._records[key]
            
            # Clean up old records
            self._cleanup_old_records(record, rule.window_seconds)
            
            status[rule_name] = {
                'current_requests': len(record.requests),
                'max_requests': rule.max_requests,
                'window_seconds': rule.window_seconds,
                'blocked_until': record.blocked_until,
                'total_blocked': record.total_blocked,
                'remaining_requests': max(0, rule.max_requests - len(record.requests))
            }
        
        return status
    
    async def cleanup_expired_records(self) -> None:
        """Periodic cleanup of expired rate limit records"""
        current_time = time.time()
        expired_keys = []
        
        for key, record in self._records.items():
            # If no recent requests and not blocked, mark for cleanup
            if (not record.requests or 
                (record.requests and current_time - record.requests[-1] > 7200) and  # 2 hours
                (not record.blocked_until or current_time > record.blocked_until)):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._records[key]
        
        print(f"🧹 Cleaned up {len(expired_keys)} expired rate limit records")

class APIRateLimiter:
    """Rate limiter for API endpoints"""
    
    def __init__(self):
        self._records: Dict[str, RateLimitRecord] = defaultdict(RateLimitRecord)
        
        # API-specific rate limit rules
        self.rules = {
            'api_per_ip': RateLimitRule(
                max_requests=100,    # 100 requests per hour per IP
                window_seconds=3600,
                burst_limit=10,      # Allow 10 quick requests
                cooldown_seconds=300
            ),
            
            'api_per_user': RateLimitRule(
                max_requests=200,    # 200 requests per hour per user
                window_seconds=3600,
                burst_limit=20,
                cooldown_seconds=300
            ),
            
            'form_generation_per_user': RateLimitRule(
                max_requests=10,     # 10 form generations per hour
                window_seconds=3600,
                cooldown_seconds=600
            ),
            
            'form_submission': RateLimitRule(
                max_requests=50,     # 50 form submissions per hour per IP
                window_seconds=3600,
                cooldown_seconds=300
            )
        }
    
    def check_and_record(self, rule_name: str, identifier: str) -> tuple[bool, str]:
        """Check rate limit and record if allowed"""
        if rule_name not in self.rules:
            return True, "No rate limit configured"
        
        rule = self.rules[rule_name]
        key = f"api_rate:{rule_name}:{hashlib.sha256(identifier.encode()).hexdigest()[:16]}"
        record = self._records[key]
        current_time = time.time()
        
        # Check cooldown
        if record.blocked_until and current_time < record.blocked_until:
            remaining = int(record.blocked_until - current_time)
            return False, f"Rate limit exceeded. Try again in {remaining} seconds."
        
        # Clear expired block
        if record.blocked_until and current_time >= record.blocked_until:
            record.blocked_until = None
        
        # Clean up old requests
        cutoff_time = current_time - rule.window_seconds
        record.requests = [req_time for req_time in record.requests if req_time > cutoff_time]
        
        # Check rate limit
        if len(record.requests) >= rule.max_requests:
            if rule.cooldown_seconds:
                record.blocked_until = current_time + rule.cooldown_seconds
                record.total_blocked += 1
            
            return False, f"Rate limit exceeded. Maximum {rule.max_requests} requests per {rule.window_seconds} seconds."
        
        # Record this request
        record.requests.append(current_time)
        return True, "Rate limit check passed"

# Global rate limiter instances
email_rate_limiter = EmailRateLimiter()
api_rate_limiter = APIRateLimiter()

# Cleanup task
async def start_cleanup_task():
    """Start background cleanup task"""
    while True:
        try:
            await asyncio.sleep(1800)  # Cleanup every 30 minutes
            await email_rate_limiter.cleanup_expired_records()
        except Exception as e:
            print(f"❌ Rate limiter cleanup error: {e}")