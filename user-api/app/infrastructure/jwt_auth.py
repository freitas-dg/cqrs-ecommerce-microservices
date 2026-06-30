from __future__ import annotations
import logging
from functools import wraps
from fastapi import Depends, HTTPException, Request, status
import jwt
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


def jwt_required(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing or invalid Authorization header.')

    token = auth_header.split(' ', 1)[1]
    settings = get_settings()
    
    jwks_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
    jwks_client = jwt.PyJWKClient(jwks_url)
    
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            options={"verify_aud": False}
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token has expired.')
    except Exception as e:
        logger.error(f"JWT Validation Error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token.')

    request.state.user_id = payload.get('sub')
    request.state.user_email = payload.get('email')
    return payload
