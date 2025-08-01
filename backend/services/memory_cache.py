"""
In-memory caching service replacement for Redis
"""
import json
import hashlib
import time
from typing import Any, Optional, Union, Dict
from datetime import datetime, timedelta
from threading import Lock


class MemoryCache:
    """Simple in-memory cache manager to replace Redis"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._lock = Lock()
        self.enabled = True
        print("✅ Memory cache initialized successfully")
    
    def _generate_key(self, prefix: str, data: Union[str, dict]) -> str:
        """Generate cache key from data"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def _is_expired(self, item: Dict) -> bool:
        """Check if cache item is expired"""
        if 'expires_at' not in item:
            return False
        return time.time() > item['expires_at']
    
    def _cleanup_expired(self):
        """Remove expired items from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self._cache.items() 
            if 'expires_at' in item and current_time > item['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            with self._lock:
                if key not in self._cache:
                    return None
                
                item = self._cache[key]
                if self._is_expired(item):
                    del self._cache[key]
                    return None
                
                return item['value']
        except Exception as e:
            print(f"❌ Memory cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        if not self.enabled:
            return False
        
        try:
            with self._lock:
                # Periodic cleanup
                if len(self._cache) % 100 == 0:
                    self._cleanup_expired()
                
                expires_at = time.time() + ttl if ttl > 0 else None
                self._cache[key] = {
                    'value': value,
                    'expires_at': expires_at,
                    'created_at': time.time()
                }
                return True
        except Exception as e:
            print(f"❌ Memory cache set error: {e}")
            return False
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                return True
        except Exception as e:
            print(f"❌ Memory cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern (simple prefix matching)"""
        if not self.enabled:
            return False
        
        try:
            with self._lock:
                keys_to_delete = [
                    key for key in self._cache.keys() 
                    if key.startswith(pattern.replace('*', ''))
                ]
                for key in keys_to_delete:
                    del self._cache[key]
                return True
        except Exception as e:
            print(f"❌ Memory cache clear pattern error: {e}")
            return False
    
    async def cache_form_generation(self, prompt: str, lang: str, html: str, ttl: int = 1800):
        """Cache form generation result"""
        cache_key = self._generate_key("form_gen", {"prompt": prompt, "lang": lang})
        cache_data = {
            "html": html,
            "generated_at": datetime.now().isoformat(),
            "prompt": prompt,
            "lang": lang
        }
        await self.set(cache_key, cache_data, ttl)
        return cache_key
    
    async def get_cached_form(self, prompt: str, lang: str) -> Optional[dict]:
        """Get cached form generation result"""
        cache_key = self._generate_key("form_gen", {"prompt": prompt, "lang": lang})
        return await self.get(cache_key)
    
    async def cache_user_session(self, user_id: str, session_data: dict, ttl: int = 86400):
        """Cache user session data"""
        cache_key = f"user_session:{user_id}"
        await self.set(cache_key, session_data, ttl)
    
    async def get_user_session(self, user_id: str) -> Optional[dict]:
        """Get cached user session"""
        cache_key = f"user_session:{user_id}"
        return await self.get(cache_key)
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all user-related cache"""
        patterns = [
            f"user_session:{user_id}",
            f"user_forms:{user_id}",
            f"user_stats:{user_id}"
        ]
        for pattern in patterns:
            await self.clear_pattern(pattern)
    
    async def cache_api_response(self, endpoint: str, params: dict, response: Any, ttl: int = 600):
        """Cache API response"""
        cache_key = self._generate_key(f"api:{endpoint}", params)
        cache_data = {
            "response": response,
            "cached_at": datetime.now().isoformat(),
            "endpoint": endpoint,
            "params": params
        }
        await self.set(cache_key, cache_data, ttl)
    
    async def get_cached_api_response(self, endpoint: str, params: dict) -> Optional[Any]:
        """Get cached API response"""
        cache_key = self._generate_key(f"api:{endpoint}", params)
        cached_data = await self.get(cache_key)
        return cached_data["response"] if cached_data else None
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            with self._lock:
                total_items = len(self._cache)
                expired_items = sum(1 for item in self._cache.values() if self._is_expired(item))
                active_items = total_items - expired_items
                
                return {
                    "enabled": True,
                    "type": "memory",
                    "total_items": total_items,
                    "active_items": active_items,
                    "expired_items": expired_items,
                    "memory_usage": "In-memory storage"
                }
        except Exception as e:
            return {"enabled": False, "error": str(e)}


# Global cache instance
cache = MemoryCache()


# Decorator for caching function results
def cache_result(ttl: int = 3600, key_prefix: str = "func"):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = cache._generate_key(
                f"{key_prefix}:{func.__name__}",
                {"args": str(args), "kwargs": str(kwargs)}
            )
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                print(f"🎯 Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            print(f"💾 Cached result for {func.__name__}")
            return result
        
        return wrapper
    return decorator