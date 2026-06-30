from __future__ import annotations
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.use_cases import UserUseCases
from app.infrastructure.auth_service import AuthService
from app.infrastructure.database import get_db_session
from app.infrastructure.elasticsearch_adapter import ElasticsearchAdapter
from app.infrastructure.encryption import EncryptionService
from app.infrastructure.jwt_auth import jwt_required
from app.infrastructure.rabbitmq import RabbitMQPublisher
from app.infrastructure.redis_cache import RedisCache
from app.infrastructure.user_repository import PostgresUserRepository
from app.presentation.schemas import MessageResponse, UserCreateRequest, UserResponse, UserUpdateRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/v1/users', tags=['Users'])
_cache: RedisCache | None = None
_search: ElasticsearchAdapter | None = None
_publisher: RabbitMQPublisher | None = None
_encryption: EncryptionService | None = None
_auth_service: AuthService | None = None

def init_dependencies(cache: RedisCache, search: ElasticsearchAdapter, publisher: RabbitMQPublisher, encryption: EncryptionService, auth_service: AuthService) -> None:
    global _cache, _search, _publisher, _encryption, _auth_service
    _cache = cache
    _search = search
    _publisher = publisher
    _encryption = encryption
    _auth_service = auth_service

def _get_use_cases(session: AsyncSession=Depends(get_db_session)) -> UserUseCases:
    repo = PostgresUserRepository(session, _encryption)
    return UserUseCases(repository=repo, cache=_cache, search=_search, event_publisher=_publisher, auth_service=_auth_service)

@router.post('', response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary='Create a new user')
async def create_user(body: UserCreateRequest, use_cases: UserUseCases=Depends(_get_use_cases)):
    try:
        user = await use_cases.create_user(name=body.name, cpf=body.cpf, email=body.email, phone_number=body.phone_number, password=body.password)
        return UserResponse(id=user.id, name=user.name, cpf=user.cpf, email=user.email, phone_number=user.phone_number, created_at=user.created_at, updated_at=user.updated_at)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get('', response_model=List[UserResponse], summary='List all users', dependencies=[Depends(jwt_required)])
async def list_users(skip: int=Query(0, ge=0, description='Offset for pagination'), limit: int=Query(100, ge=1, le=500, description='Max results per page'), use_cases: UserUseCases=Depends(_get_use_cases)):
    users = await use_cases.list_users(skip=skip, limit=limit)
    return [UserResponse(id=u.id, name=u.name, cpf=u.cpf, email=u.email, phone_number=u.phone_number, created_at=u.created_at, updated_at=u.updated_at) for u in users]

@router.get('/search', response_model=List[dict], summary='Search users via Elasticsearch', dependencies=[Depends(jwt_required)])
async def search_users(q: str=Query(..., min_length=1, description='Search query'), use_cases: UserUseCases=Depends(_get_use_cases)):
    return await use_cases.search_users(q)

@router.get('/{user_id}', response_model=UserResponse, summary='Get user by ID', dependencies=[Depends(jwt_required)])
async def get_user(user_id: str, use_cases: UserUseCases=Depends(_get_use_cases)):
    user = await use_cases.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id {user_id} not found.')
    return UserResponse(id=user.id, name=user.name, cpf=user.cpf, email=user.email, phone_number=user.phone_number, created_at=user.created_at, updated_at=user.updated_at)

@router.put('/{user_id}', response_model=UserResponse, summary='Update user', dependencies=[Depends(jwt_required)])
async def update_user(user_id: str, body: UserUpdateRequest, use_cases: UserUseCases=Depends(_get_use_cases)):
    try:
        user = await use_cases.update_user(user_id=user_id, name=body.name, email=body.email, phone_number=body.phone_number)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id {user_id} not found.')
    return UserResponse(id=user.id, name=user.name, cpf=user.cpf, email=user.email, phone_number=user.phone_number, created_at=user.created_at, updated_at=user.updated_at)

@router.delete('/{user_id}', response_model=MessageResponse, summary='Delete user', dependencies=[Depends(jwt_required)])
async def delete_user(user_id: str, use_cases: UserUseCases=Depends(_get_use_cases)):
    deleted = await use_cases.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id {user_id} not found.')
    return MessageResponse(message=f'User {user_id} deleted successfully.')
