"""Redis cache manager for efficient data caching."""
import json
from typing import Any, Optional, Union
import redis.asyncio as redis
from datetime import timedelta
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis caching with JSON serialization."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache manager with Redis connection.
        
        Args:
            redis_url: Redis connection URL, defaults to settings
        """
        self.redis_url = redis_url or settings.redis_url
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Establish Redis connection."""
        if not self._redis:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis cache")
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self._redis:
            await self.connect()
        
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds or timedelta
            
        Returns:
            True if successful, False otherwise
        """
        if not self._redis:
            await self.connect()
        
        try:
            json_value = json.dumps(value, default=str)
            
            if ttl is None:
                ttl = settings.cache_ttl_seconds
            elif isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            await self._redis.setex(key, ttl, json_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        if not self._redis:
            await self.connect()
        
        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        if not self._redis:
            await self.connect()
        
        try:
            result = await self._redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        if not self._redis:
            await self.connect()
        
        try:
            values = await self._redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(
        self, 
        mapping: dict[str, Any], 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set multiple key-value pairs in cache.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live for all keys
            
        Returns:
            True if all successful, False otherwise
        """
        if not self._redis:
            await self.connect()
        
        try:
            pipe = self._redis.pipeline()
            
            if ttl is None:
                ttl = settings.cache_ttl_seconds
            elif isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            for key, value in mapping.items():
                json_value = json.dumps(value, default=str)
                pipe.setex(key, ttl, json_value)
            
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "odds:*")
            
        Returns:
            Number of keys deleted
        """
        if not self._redis:
            await self.connect()
        
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear_pattern error for pattern {pattern}: {e}")
            return 0
    
    async def warm_cache(self, data: dict[str, Any], prefix: str = "") -> None:
        """Pre-populate cache with data.
        
        Args:
            data: Dictionary of data to cache
            prefix: Optional prefix for cache keys
        """
        mapping = {}
        for key, value in data.items():
            cache_key = f"{prefix}{key}" if prefix else key
            mapping[cache_key] = value
        
        await self.set_many(mapping)
        logger.info(f"Warmed cache with {len(mapping)} entries")


# Global cache instance
cache_manager = CacheManager()