from __future__ import annotations
import logging
from typing import Optional
from app.domain.repositories import UserRepositoryInterface
from app.infrastructure.auth_service import AuthService

logger = logging.getLogger(__name__)


class AuthUseCases:

    def __init__(self, repository: UserRepositoryInterface, auth_service: AuthService) -> None:
        self._repo = repository
        self._auth = auth_service

    async def login(self, email: str, password: str) -> dict:
        user = await self._repo.get_by_email(email)
        if not user:
            raise ValueError('Invalid email or password.')

        tokens = self._auth.create_access_token(email, password)
        
        logger.info('User authenticated via Keycloak: id=%s', user.id)
        return {
            'access_token': tokens['access_token'],
            'refresh_token': tokens.get('refresh_token'),
            'token_type': 'bearer'
        }

    async def refresh(self, refresh_token: str) -> dict:
        raise ValueError('Refresh token must be handled directly via Keycloak or implemented via backend.')
