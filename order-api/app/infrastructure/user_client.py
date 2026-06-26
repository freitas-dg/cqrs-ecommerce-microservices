import json
import logging
from typing import Optional
import pybreaker
import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from app.domain.repositories import CacheInterface, UserServiceInterface

logger = logging.getLogger(__name__)
user_api_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30, name='UserAPICircuitBreaker')
USER_CACHE_PREFIX = 'user_cache'
USER_CACHE_TTL = 600

class UserAPIClient(UserServiceInterface):

    def __init__(self, base_url: str, timeout: int, cache: CacheInterface) -> None:
        self._base_url = base_url.rstrip('/')
        self._timeout = timeout
        self._cache = cache

    def get_user(self, user_id: str) -> Optional[dict]:
        cache_key = f'{USER_CACHE_PREFIX}:{user_id}'
        cached = self._cache.get(cache_key)
        if cached:
            logger.debug('User %s found in local cache', user_id)
            return json.loads(cached)
        try:
            data = self._fetch_user_from_api(user_id)
            if data:
                self._cache.set(cache_key, json.dumps(data, default=str), USER_CACHE_TTL)
            return data
        except pybreaker.CircuitBreakerError:
            logger.warning('Circuit breaker OPEN for User API — returning None for user %s', user_id)
            return {'id': user_id, 'name': 'Unknown (Service Unavailable)', 'error': 'circuit_breaker_open'}
        except Exception as e:
            logger.error('Failed to fetch user %s: %s', user_id, e)
            return {'id': user_id, 'name': 'Unknown (Error)', 'error': str(e)}

    def user_exists(self, user_id: str) -> bool:
        try:
            data = self._fetch_user_from_api(user_id)
            return data is not None
        except (pybreaker.CircuitBreakerError, Exception) as e:
            logger.warning('Cannot verify user %s existence: %s', user_id, e)
            return True

    @user_api_breaker
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=5), retry=retry_if_exception_type(requests.ConnectionError), reraise=True)
    def _fetch_user_from_api(self, user_id: str) -> Optional[dict]:
        url = f'{self._base_url}/api/v1/users/{user_id}'
        response = requests.get(url, timeout=self._timeout)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def invalidate_user_cache(self, user_id: str) -> None:
        cache_key = f'{USER_CACHE_PREFIX}:{user_id}'
        self._cache.delete(cache_key)
        logger.info('Invalidated local cache for user %s', user_id)
