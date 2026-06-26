import logging
from typing import Optional
import redis
from app.domain.repositories import CacheInterface
logger = logging.getLogger(__name__)

class RedisCache(CacheInterface):

    def __init__(self, redis_url: str) -> None:
        self._redis = redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> Optional[str]:
        try:
            return self._redis.get(key)
        except Exception as e:
            logger.warning("Redis GET failed for '%s': %s", key, e)
            return None

    def set(self, key: str, value: str, ttl: int=300) -> None:
        try:
            self._redis.set(key, value, ex=ttl)
        except Exception as e:
            logger.warning("Redis SET failed for '%s': %s", key, e)

    def delete(self, key: str) -> None:
        try:
            self._redis.delete(key)
        except Exception as e:
            logger.warning("Redis DELETE failed for '%s': %s", key, e)

    def delete_pattern(self, pattern: str) -> None:
        try:
            cursor = 0
            while True:
                cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    self._redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning("Redis DELETE_PATTERN failed for '%s': %s", pattern, e)
