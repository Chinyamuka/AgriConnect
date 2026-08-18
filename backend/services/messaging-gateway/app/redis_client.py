"""
Redis client for the Messaging Gateway Service.

Used for:
1. USSD session storage
2. OTP code storage
3. Rate limiting
4. Caching
"""
import json
import redis.asyncio as redis
from typing import Optional, Any, Dict
from datetime import timedelta
from app.config import settings


class RedisClient:
    """
    Async Redis client wrapper.
    
    Handles connection pooling and common operations.
    """
    
    def __init__(self):
        """Initialize the Redis connection."""
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
        
        return self.client
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            await self.client.connection_pool.disconnect()
            self.client = None
            self.pool = None
    
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
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        client = await self.connect()
        return await client.exists(key) > 0
    
    async def get_json(self, key: str) -> Optional[Dict]:
        """Get a JSON value by key."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(self, key: str, value: Dict, expire_seconds: Optional[int] = None):
        """Set a JSON value."""
        await self.set(key, value, expire_seconds)
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        client = await self.connect()
        return await client.incr(key, amount)
    
    async def expire(self, key: str, seconds: int):
        """Set expiry on a key."""
        client = await self.connect()
        await client.expire(key, seconds)
    
    # ========================================================================
    # USSD SESSION METHODS
    # ========================================================================
    
    async def get_ussd_session(self, session_id: str) -> Optional[Dict]:
        """Get a USSD session."""
        key = f"ussd:session:{session_id}"
        return await self.get_json(key)
    
    async def save_ussd_session(self, session_id: str, data: Dict):
        """Save a USSD session."""
        key = f"ussd:session:{session_id}"
        await self.set_json(key, data, settings.ussd_session_timeout)
    
    async def delete_ussd_session(self, session_id: str):
        """Delete a USSD session."""
        key = f"ussd:session:{session_id}"
        await self.delete(key)
    
    # ========================================================================
    # OTP METHODS
    # ========================================================================
    
    async def save_otp(self, phone: str, code: str, purpose: str = "verification"):
        """Save an OTP code."""
        key = f"otp:{phone}:{purpose}"
        await self.set(key, code, settings.otp_expiry_seconds)
    
    async def get_otp(self, phone: str, purpose: str = "verification") -> Optional[str]:
        """Get an OTP code."""
        key = f"otp:{phone}:{purpose}"
        return await self.get(key)
    
    async def delete_otp(self, phone: str, purpose: str = "verification"):
        """Delete an OTP code."""
        key = f"otp:{phone}:{purpose}"
        await self.delete(key)


# Create a singleton instance
redis_client = RedisClient()
