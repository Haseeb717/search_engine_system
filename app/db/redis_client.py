"""
Redis client for caching search results and session data.
"""
import json
from typing import Optional, Any
import redis.asyncio as aioredis
from app.core.config import settings


class RedisClient:
    """Async Redis client wrapper for caching operations."""
    
    def __init__(self):
        self.client: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Establish connection to Redis."""
        self.client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        print(f"✅ Connected to Redis at {settings.redis_host}:{settings.redis_port}")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            print("✅ Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.client:
            return None
        
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default from settings)
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        ttl = ttl or settings.redis_cache_ttl
        
        # Serialize non-string values
        if not isinstance(value, str):
            value = json.dumps(value)
        
        await self.client.setex(key, ttl, value)
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.client:
            return False
        
        await self.client.delete(key)
        return True
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.client:
            return False
        
        result = await self.client.exists(key)
        return bool(result) if result is not None else False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "search:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        keys = await self.client.keys(pattern)
        if keys:
            result = await self.client.delete(*keys)
            return int(result) if result is not None else 0
        return 0


# Global Redis client instance
redis_client = RedisClient()