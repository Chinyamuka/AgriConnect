"""
================================================================================
REDIS CLIENT FOR BIDDING SERVICE
================================================================================

Used for:
1. Distributed locks - prevent double-selling
2. Caching - frequently accessed data
3. Rate limiting - prevent abuse

Why Redis for locks?
1. Atomic operations (SETNX)
2. TTL support (auto-release)
3. Distributed (works across multiple instances)
4. Fast (in-memory)

================================================================================
"""
import redis.asyncio as redis
from typing import Optional, Any
import json
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client wrapper.
    
    Handles connection pooling and common operations.
    """
    
    def __init__(self):
        self.pool = None
        self.client = None
    
    async def connect(self):
        """Establish connection to Redis."""
        if not self.client:
            self.pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=10,
                decode_responses=True
            )
            self.client = redis.Redis(connection_pool=self.pool)
            logger.info("✅ Connected to Redis")
        return self.client
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            await self.client.connection_pool.disconnect()
            self.client = None
            self.pool = None
    
    # ========================================================================
    # LOCK METHODS (Distributed Lock)
    # ========================================================================
    async def acquire_lock(self, lock_key: str, timeout: int = 30) -> bool:
        """
        Acquire a distributed lock.
        
        Uses Redis SETNX (Set if Not eXists) with TTL.
        
        Args:
            lock_key: Unique key for the lock (e.g., "lock:listing:123")
            timeout: Lock timeout in seconds (auto-release)
        
        Returns:
            bool: True if lock acquired, False if already locked
        
        Why:
            - Prevents double-selling of a listing
            - Only one bid can be accepted at a time
            - Auto-release prevents deadlocks
        """
        client = await self.connect()
        # SETNX with TTL
        # Returns True if key was set (lock acquired)
        # Returns False if key already exists (lock held by someone else)
        acquired = await client.set(lock_key, "locked", nx=True, ex=timeout)
        if acquired:
            logger.info(f"🔒 Lock acquired: {lock_key}")
        else:
            logger.info(f"🔒 Lock already held: {lock_key}")
        return acquired
    
    async def release_lock(self, lock_key: str) -> bool:
        """
        Release a distributed lock.
        
        Args:
            lock_key: Key of the lock to release
        
        Returns:
            bool: True if released, False if not found
        """
        client = await self.connect()
        deleted = await client.delete(lock_key)
        if deleted:
            logger.info(f"🔓 Lock released: {lock_key}")
        return bool(deleted)
    
    async def is_locked(self, lock_key: str) -> bool:
        """
        Check if a lock exists.
        
        Args:
            lock_key: Key to check
        
        Returns:
            bool: True if locked, False if not
        """
        client = await self.connect()
        return await client.exists(lock_key) > 0
    
    # ========================================================================
    # CACHE METHODS
    # ========================================================================
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        client = await self.connect()
        return await client.get(key)
    
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None):
        """Set a value with optional expiry."""
        client = await self.connect()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await client.set(key, value, ex=expire_seconds)
    
    async def delete(self, key: str):
        """Delete a key."""
        client = await self.connect()
        await client.delete(key)


# Create a singleton instance
redis_client = RedisClient()
