"""
Redis caching service for improved performance
"""
import redis
import json
import hashlib
from typing import Any, Optional, Union
from datetime import datetime, timedelta
from backend.config import get_settings

settings = get_settings()


class RedisCache:
    """Redis cache manager"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            if hasattr(settings, 'redis_url') and settings.redis_url:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                print("✅ Redis cache initialized successfully")
            else:
                print("ℹ️ Redis URL not configured, caching disabled")
        except Exception as e:
            print(f"⚠️ Redis initialization failed: {e}")
            self.enabled = False
    
    def _generate_key(self, prefix: str, data: Union[str, dict]) -> str:
        """Generate cache key from data"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"❌ Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        if not self.enabled:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            print(f"❌ Redis set error: {e}")
            return False
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Redis delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.enabled:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"❌ Redis clear pattern error: {e}")
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
        if not self.enabled:
            return {"enabled": False, "message": "Redis not available"}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "N/A"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_ratio": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 2
                )
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}


# Global cache instance
cache = RedisCache()


# Decorator for caching function results
def cache_result(ttl: int = 3600, key_prefix: str = "func"):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = cache._generate_key(
                f"{key_prefix}:{func.__name__}",
                {"args": args, "kwargs": kwargs}
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