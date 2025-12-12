import json
from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as aioredis

from services.reputation_lookup.models import (
    DomainReputationResponse,
    IPReputationResponse,
)


class ReputationCache:
    """Redis-based cache for reputation lookups"""

    def __init__(self, redis_url: str = "redis://localhost:6379", ttl_seconds: int = 3600):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        self.redis = await aioredis.from_url(
            self.redis_url, encoding="utf-8", decode_responses=True
        )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()

    def _make_key(self, indicator_type: str, indicator: str) -> str:
        """Generate cache key"""
        return f"reputation:{indicator_type}:{indicator}"

    async def get_ip(self, ip_address: str) -> Optional[IPReputationResponse]:
        """Get cached IP reputation"""
        if not self.redis:
            return None

        key = self._make_key("ip", ip_address)
        data = await self.redis.get(key)

        if data:
            try:
                parsed = json.loads(data)
                return IPReputationResponse(**parsed)
            except Exception:
                return None

        return None

    async def set_ip(self, ip_address: str, response: IPReputationResponse):
        """Cache IP reputation"""
        if not self.redis:
            return

        key = self._make_key("ip", ip_address)
        response.cached = True
        data = response.model_dump_json()
        await self.redis.setex(key, self.ttl_seconds, data)

    async def get_domain(self, domain: str) -> Optional[DomainReputationResponse]:
        """Get cached domain reputation"""
        if not self.redis:
            return None

        key = self._make_key("domain", domain)
        data = await self.redis.get(key)

        if data:
            try:
                parsed = json.loads(data)
                return DomainReputationResponse(**parsed)
            except Exception:
                return None

        return None

    async def set_domain(self, domain: str, response: DomainReputationResponse):
        """Cache domain reputation"""
        if not self.redis:
            return

        key = self._make_key("domain", domain)
        response.cached = True
        data = response.model_dump_json()
        await self.redis.setex(key, self.ttl_seconds, data)

    async def invalidate(self, indicator: str):
        """Invalidate cache for an indicator"""
        if not self.redis:
            return

        keys = [
            self._make_key("ip", indicator),
            self._make_key("domain", indicator),
        ]
        await self.redis.delete(*keys)

    async def clear_all(self):
        """Clear all reputation cache entries"""
        if not self.redis:
            return

        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor=cursor, match="reputation:*", count=100
            )
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.redis:
            return {"error": "Redis not connected"}

        info = await self.redis.info("stats")
        return {
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "total_keys": await self.redis.dbsize(),
        }
