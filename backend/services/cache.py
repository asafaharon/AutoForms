import asyncio
import json
import hashlib
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

class SimpleCache:
    """Simple in-memory cache for OpenAI responses"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
    def _generate_key(self, prompt: str, model: str, temperature: float) -> str:
        """Generate cache key from prompt and parameters - using faster hash"""
        # Use built-in hash() for speed, normalize prompt for better cache hits
        normalized_prompt = prompt.lower().strip()
        content = f"{normalized_prompt}:{model}:{temperature}"
        return str(hash(content))
    
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """Check if cache item is expired"""
        expiry = item.get("expiry")
        if not expiry:
            return True
        return datetime.now() > expiry
    
    def _cleanup_expired(self):
        """Remove expired items from cache"""
        expired_keys = [
            key for key, item in self.cache.items() 
            if self._is_expired(item)
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def get(self, prompt: str, model: str, temperature: float) -> Optional[Any]:
        """Get cached response if available and not expired"""
        key = self._generate_key(prompt, model, temperature)
        
        if key not in self.cache:
            return None
            
        item = self.cache[key]
        if self._is_expired(item):
            del self.cache[key]
            return None
            
        # Update access time for LRU-style behavior
        item["last_accessed"] = datetime.now()
        return item["data"]
    
    def set(self, prompt: str, model: str, temperature: float, data: Any):
        """Cache response with TTL"""
        key = self._generate_key(prompt, model, temperature)
        
        # Cleanup expired items
        self._cleanup_expired()
        
        # If cache is full, remove least recently accessed item
        if len(self.cache) >= self.max_size:
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].get("last_accessed", datetime.min)
            )
            del self.cache[oldest_key]
        
        self.cache[key] = {
            "data": data,
            "expiry": datetime.now() + timedelta(seconds=self.ttl_seconds),
            "last_accessed": datetime.now()
        }
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)

# Global cache instance - optimized for performance
openai_cache = SimpleCache(max_size=200, ttl_seconds=7200)  # 2 hours TTL, larger cache