"""
Redis cache configuration and client setup.
"""

import json
import pickle
import logging
from typing import Optional, Any, Union
from functools import wraps
import redis.asyncio as redis
from fastapi import FastAPI
import asyncio

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client with async support."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
    
    async def init(
        self, 
        redis_url: str = "redis://localhost:6379",
        max_connections: int = 20,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30
    ):
        """Initialize Redis connection with connection pooling."""
        try:
            # Create connection pool
            connection_pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=max_connections,
                retry_on_timeout=retry_on_timeout,
                health_check_interval=health_check_interval
            )
            
            self.redis_client = redis.Redis(
                connection_pool=connection_pool,
                decode_responses=False  # Keep bytes for pickle compatibility
            )
            
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("✅ Redis cache initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis cache: {e}")
            self.is_connected = False
            raise
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("🔌 Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_connected:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"❌ Error getting cache key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = 3600,
        serialize_method: str = "json"
    ) -> bool:
        """Set value in cache with TTL."""
        if not self.is_connected:
            return False
        
        try:
            if serialize_method == "json":
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = pickle.dumps(value)
            
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"❌ Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_connected:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"❌ Error deleting cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.is_connected:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"❌ Error checking cache key {key}: {e}")
            return False
    
    async def clear(self, pattern: str = "*") -> int:
        """Clear cache keys matching pattern."""
        if not self.is_connected:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"❌ Error clearing cache pattern {pattern}: {e}")
            return 0
    
    async def health_check(self) -> dict:
        """Check Redis health status."""
        try:
            if not self.redis_client:
                return {"status": "disconnected", "error": "No Redis client"}
            
            # Test ping
            await self.redis_client.ping()
            
            # Get info
            info = await self.redis_client.info()
            
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global cache instance
cache = RedisCache()


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    serialize_method: str = "json"
):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        serialize_method: 'json' or 'pickle'
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:"
            
            # Add args and kwargs to key
            key_parts = []
            for arg in args:
                if hasattr(arg, 'id'):  # For model instances
                    key_parts.append(f"{type(arg).__name__}_{arg.id}")
                else:
                    key_parts.append(str(arg)[:50])  # Limit length
            
            for k, v in kwargs.items():
                key_parts.append(f"{k}_{v}")
            
            cache_key += "_".join(key_parts)
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl, serialize_method)
            logger.debug(f"💾 Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator


async def init_cache(app: FastAPI, redis_url: str = "redis://localhost:6379"):
    """Initialize cache on app startup."""
    try:
        await cache.init(redis_url)
        app.state.cache = cache
        logger.info("🚀 Cache initialized in FastAPI app")
    except Exception as e:
        logger.error(f"❌ Failed to initialize cache: {e}")
        raise


async def close_cache():
    """Close cache on app shutdown."""
    await cache.close()
    logger.info("🔌 Cache closed")


# Cache dependency for FastAPI
async def get_cache() -> RedisCache:
    """FastAPI dependency to get cache instance."""
    return cache
