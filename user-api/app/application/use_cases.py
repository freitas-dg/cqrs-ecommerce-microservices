from __future__ import annotations
import json
import logging
from typing import List, Optional
from app.domain.entities import User
from app.domain.repositories import CacheInterface, EventPublisherInterface, SearchInterface, UserRepositoryInterface
from app.infrastructure.auth_service import AuthService

logger = logging.getLogger(__name__)
CACHE_PREFIX = 'user'
CACHE_LIST_KEY = f'{CACHE_PREFIX}:list'
CACHE_TTL = 300

class UserUseCases:

    def __init__(self, repository: UserRepositoryInterface, cache: CacheInterface, search: SearchInterface, event_publisher: EventPublisherInterface, auth_service: AuthService) -> None:
        self._repo = repository
        self._cache = cache
        self._search = search
        self._events = event_publisher
        self._auth = auth_service

    async def create_user(self, name: str, cpf: str, email: str, phone_number: str, password: str) -> User:
        existing = await self._repo.get_by_cpf(cpf)
        if existing:
            raise ValueError(f'User with CPF {cpf} already exists.')

        kc_id = self._auth.create_user_in_keycloak(email, password, name)

        user = User(id=kc_id, name=name, cpf=cpf, email=email, phone_number=phone_number)
        
        created_user = await self._repo.create(user)
        await self._cache.delete_pattern(f'{CACHE_LIST_KEY}:*')
        await self._events.publish('user.created', self._user_to_dict(created_user))
        logger.info('User created: id=%s, cpf=%s', created_user.id, cpf)
        return created_user

    async def get_user(self, user_id: str) -> Optional[User]:
        cache_key = f'{CACHE_PREFIX}:{user_id}'
        cached = await self._cache.get(cache_key)
        if cached:
            logger.debug('Cache hit for user %s', user_id)
            return self._dict_to_user(json.loads(cached))

        user = await self._repo.get_by_id(user_id)
        if user:
            await self._cache.set(cache_key, json.dumps(self._user_to_dict(user)), CACHE_TTL)
        return user

    async def list_users(self, skip: int=0, limit: int=100) -> List[User]:
        cache_key = f'{CACHE_LIST_KEY}:{skip}:{limit}'
        cached = await self._cache.get(cache_key)
        if cached:
            logger.debug('Cache hit for user list (skip=%s, limit=%s)', skip, limit)
            return [self._dict_to_user(u) for u in json.loads(cached)]

        users = await self._repo.list_all(skip=skip, limit=limit)
        if users:
            await self._cache.set(cache_key, json.dumps([self._user_to_dict(u) for u in users]), CACHE_TTL)
        return users

    async def update_user(self, user_id: str, name: Optional[str]=None, email: Optional[str]=None, phone_number: Optional[str]=None) -> Optional[User]:
        user = await self._repo.get_by_id(user_id)
        if not user:
            return None

        user.update(name=name, email=email, phone_number=phone_number)
        updated_user = await self._repo.update(user)
        await self._cache.delete(f'{CACHE_PREFIX}:{user_id}')
        await self._cache.delete_pattern(f'{CACHE_LIST_KEY}:*')
        await self._events.publish('user.updated', self._user_to_dict(updated_user))
        logger.info('User updated: id=%s', user_id)
        return updated_user

    async def delete_user(self, user_id: str) -> bool:
        deleted = await self._repo.delete(user_id)
        if not deleted:
            return False

        await self._cache.delete(f'{CACHE_PREFIX}:{user_id}')
        await self._cache.delete_pattern(f'{CACHE_LIST_KEY}:*')
        await self._events.publish('user.deleted', {'id': user_id})
        logger.info('User deleted: id=%s', user_id)
        return True

    async def search_users(self, query: str) -> List[dict]:
        return await self._search.search_users(query)

    @staticmethod
    def _user_to_dict(user: User) -> dict:
        return {'id': user.id, 'name': user.name, 'cpf': user.cpf, 'email': user.email, 'phone_number': user.phone_number, 'created_at': user.created_at.isoformat() if user.created_at else None, 'updated_at': user.updated_at.isoformat() if user.updated_at else None}

    @staticmethod
    def _dict_to_user(data: dict) -> User:
        from datetime import datetime
        return User(id=data.get('id'), name=data['name'], cpf=data['cpf'], email=data['email'], phone_number=data['phone_number'], created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None, updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None)
