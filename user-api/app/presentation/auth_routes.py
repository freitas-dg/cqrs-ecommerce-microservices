from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.auth_use_cases import AuthUseCases
from app.infrastructure.auth_service import AuthService
from app.infrastructure.database import get_db_session
from app.infrastructure.encryption import EncryptionService
from app.infrastructure.user_repository import PostgresUserRepository
from app.presentation.schemas import LoginRequest, RefreshRequest, TokenResponse

logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix='/api/v1/auth', tags=['Authentication'])
_auth_service: AuthService | None = None
_encryption: EncryptionService | None = None


def init_auth_dependencies(auth_service: AuthService, encryption: EncryptionService) -> None:
    global _auth_service, _encryption
    _auth_service = auth_service
    _encryption = encryption


def _get_auth_use_cases(session: AsyncSession = Depends(get_db_session)) -> AuthUseCases:
    repo = PostgresUserRepository(session, _encryption)
    return AuthUseCases(repository=repo, auth_service=_auth_service)


@auth_router.post('/login', response_model=TokenResponse, summary='Authenticate and obtain JWT tokens')
async def login(body: LoginRequest, use_cases: AuthUseCases = Depends(_get_auth_use_cases)):
    try:
        tokens = await use_cases.login(email=body.email, password=body.password)
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@auth_router.post('/refresh', response_model=TokenResponse, summary='Refresh an access token')
async def refresh(body: RefreshRequest, use_cases: AuthUseCases = Depends(_get_auth_use_cases)):
    try:
        tokens = await use_cases.refresh(refresh_token=body.refresh_token)
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
