from __future__ import annotations
import logging
from functools import wraps
from flask import current_app, g, jsonify, request
import jwt

logger = logging.getLogger(__name__)


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header.'}), 401

        token = auth_header.split(' ', 1)[1]
        
        jwks_url = f"{current_app.config['KEYCLOAK_URL']}/realms/{current_app.config['KEYCLOAK_REALM']}/protocol/openid-connect/certs"
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
            return jsonify({'error': 'Token has expired.'}), 401
        except Exception as e:
            logger.error(f"JWT Validation Error: {e}")
            return jsonify({'error': 'Invalid token.'}), 401

        g.current_user_id = payload.get('sub')
        g.current_user_email = payload.get('email')
        return f(*args, **kwargs)

    return decorated
