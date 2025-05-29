"""
Redis client configuration and utilities
"""

import json
import time
from typing import Any, Optional
from urllib.parse import urlparse

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection pooling
    """
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """
        Initialize Redis connection pool
        """
        try:
            # Parse Redis URL
            parsed_url = urlparse(settings.REDIS_URL)
            
            # Create connection pool
            self._pool = ConnectionPool(
                host=parsed_url.hostname or "localhost",
                port=parsed_url.port or 6379,
                password=parsed_url.password,
                db=int(parsed_url.path.lstrip("/") or 0),
                max_connections=settings.REDIS_POOL_SIZE,
                decode_responses=True,
            )
            
            # Create client
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def close(self):
        """
        Close Redis connection
        """
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
    
    @property
    def client(self) -> redis.Redis:
        """
        Get Redis client instance
        """
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return self._client
    
    # Cache operations
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache
        """
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error("Redis get error", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional expiration
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if expire:
                return await self._client.setex(key, expire, value)
            else:
                return await self._client.set(key, value)
        except Exception as e:
            logger.error("Redis set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        """
        try:
            return bool(await self._client.delete(key))
        except Exception as e:
            logger.error("Redis delete error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists
        """
        try:
            return bool(await self._client.exists(key))
        except Exception as e:
            logger.error("Redis exists error", key=key, error=str(e))
            return False
    
    # Session operations
    async def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data
        """
        key = f"session:{session_id}"
        data = await self.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_session(
        self,
        session_id: str,
        data: dict,
        expire: int = 3600
    ) -> bool:
        """
        Set session data with expiration
        """
        key = f"session:{session_id}"
        return await self.set(key, data, expire)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        """
        key = f"session:{session_id}"
        return await self.delete(key)
    
    # Room operations
    async def add_room_participant(
        self,
        room_id: str,
        participant_id: str,
        data: dict
    ) -> bool:
        """
        Add participant to room
        """
        key = f"room:{room_id}:participants"
        try:
            await self._client.hset(key, participant_id, json.dumps(data))
            # Set expiration for 24 hours
            await self._client.expire(key, 86400)
            return True
        except Exception as e:
            logger.error(
                "Failed to add room participant",
                room_id=room_id,
                participant_id=participant_id,
                error=str(e)
            )
            return False
    
    async def remove_room_participant(
        self,
        room_id: str,
        participant_id: str
    ) -> bool:
        """
        Remove participant from room
        """
        key = f"room:{room_id}:participants"
        try:
            await self._client.hdel(key, participant_id)
            return True
        except Exception as e:
            logger.error(
                "Failed to remove room participant",
                room_id=room_id,
                participant_id=participant_id,
                error=str(e)
            )
            return False
    
    async def get_room_participants(self, room_id: str) -> dict:
        """
        Get all participants in a room
        """
        key = f"room:{room_id}:participants"
        try:
            data = await self._client.hgetall(key)
            return {
                pid: json.loads(pdata)
                for pid, pdata in data.items()
            }
        except Exception as e:
            logger.error(
                "Failed to get room participants",
                room_id=room_id,
                error=str(e)
            )
            return {}
    
    # Rate limiting
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, int]:
        """
        Check rate limit using sliding window
        Returns (allowed, remaining)
        """
        try:
            pipe = self._client.pipeline()
            now = int(time.time())
            window_start = now - window
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Count requests in window
            pipe.zcard(key)
            # Set expiration
            pipe.expire(key, window)
            
            results = await pipe.execute()
            count = results[2]
            
            if count > limit:
                # Remove the just-added entry
                await self._client.zrem(key, str(now))
                return False, 0
            
            return True, limit - count
        except Exception as e:
            logger.error("Rate limit check error", key=key, error=str(e))
            # Allow request on error
            return True, limit


# Global Redis client instance
redis_client = RedisClient()


# Helper functions
async def get_redis() -> redis.Redis:
    """
    Get Redis client for dependency injection
    """
    return redis_client.client 