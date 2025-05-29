"""
Redis client configuration
"""

import redis.asyncio as redis
from typing import Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RedisClient:
    """
    Redis client wrapper
    """
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize Redis connection
        """
        if self._initialized:
            return
            
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            
            self._initialized = True
            logger.info("Redis client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Redis client", error=str(e))
            # Don't raise - Redis is optional
            self.redis = None
    
    async def close(self):
        """
        Close Redis connection
        """
        if self.redis:
            await self.redis.close()
            self._initialized = False
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis
        """
        if not self.redis:
            return None
            
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error("Redis get error", error=str(e), key=key)
            return None
    
    async def set(self, key: str, value: str, expire: int = None) -> bool:
        """
        Set value in Redis
        """
        if not self.redis:
            return False
            
        try:
            await self.redis.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error("Redis set error", error=str(e), key=key)
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis
        """
        if not self.redis:
            return False
            
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("Redis delete error", error=str(e), key=key)
            return False


# Global Redis client instance
redis_client = RedisClient() 