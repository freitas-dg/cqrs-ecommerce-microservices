from __future__ import annotations
import logging
from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities import User
from app.domain.repositories import UserRepositoryInterface
from app.infrastructure.encryption import EncryptionService
from app.infrastructure.models import UserModel

logger = logging.getLogger(__name__)

class PostgresUserRepository(UserRepositoryInterface):

    def __init__(self, session: AsyncSession, encryption: EncryptionService) -> None:
        self._session = session
        self._enc = encryption

    async def create(self, user: User) -> User:
        model = UserModel(id=user.id, name=user.name, cpf=self._enc.encrypt(user.cpf), email=self._enc.encrypt(user.email), phone_number=self._enc.encrypt(user.phone_number))
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_cpf(self, cpf: str) -> Optional[User]:
        encrypted_cpf = self._enc.encrypt(cpf)
        result = await self._session.execute(select(UserModel))
        models = result.scalars().all()
        for model in models:
            if self._enc.decrypt(model.cpf) == cpf:
                return self._to_entity(model)
        return None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(select(UserModel))
        models = result.scalars().all()
        for model in models:
            if self._enc.decrypt(model.email) == email:
                return self._to_entity(model)
        return None

    async def list_all(self, skip: int=0, limit: int=100) -> List[User]:
        result = await self._session.execute(select(UserModel).order_by(UserModel.id).offset(skip).limit(limit))
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def update(self, user: User) -> User:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user.id))
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f'User with id {user.id} not found.')
        model.name = user.name
        model.email = self._enc.encrypt(user.email)
        model.phone_number = self._enc.encrypt(user.phone_number)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, user_id: str) -> bool:
        result = await self._session.execute(delete(UserModel).where(UserModel.id == user_id))
        return result.rowcount > 0

    def _to_entity(self, model: UserModel) -> User:
        return User(id=model.id, name=model.name, cpf=self._enc.decrypt(model.cpf), email=self._enc.decrypt(model.email), phone_number=self._enc.decrypt(model.phone_number), created_at=model.created_at, updated_at=model.updated_at)
