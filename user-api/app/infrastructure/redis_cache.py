import logging
from typing import Optional
import redis.asyncio as aioredis
from app.domain.repositories import CacheInterface
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)

class RedisCache(CacheInterface):

    def __init__(self) -> None:
        settings = get_settings()
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        try:
            return await self._redis.get(key)
        except Exception as e:
            logger.warning("Redis GET failed for key '%s': %s", key, e)
            return None

    async def set(self, key: str, value: str, ttl: int=300) -> None:
        try:
            await self._redis.set(key, value, ex=ttl)
        except Exception as e:
            logger.warning("Redis SET failed for key '%s': %s", key, e)

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.warning("Redis DELETE failed for key '%s': %s", key, e)

    async def delete_pattern(self, pattern: str) -> None:
        try:
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning("Redis DELETE_PATTERN failed for '%s': %s", pattern, e)

    async def close(self) -> None:
        await self._redis.close()
