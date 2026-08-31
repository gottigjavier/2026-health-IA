"""
WebSocket JWT authentication helper.

Validates the JWT access token sent as query parameter (?token=<access>)
and returns the authenticated Django user.

Compatible with the token format emitted by ninja_jwt (RefreshToken.for_user).
Uses the same SIGNING_KEY and ALGORITHM from NINJA_JWT settings.
"""

import logging
from urllib.parse import parse_qs

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

# WebSocket close codes for auth rejection (application-range 4400-4499)
WS_CLOSE_CODE_MISSING_TOKEN = 4401
WS_CLOSE_CODE_INVALID_TOKEN = 4402


def extract_token_from_scope(scope):
    """
    Extract the 'token' query parameter from the WebSocket scope.

    The frontend sends the JWT as: ws://host/ws/<path>?token=<access_token>

    Returns the token string or None if absent.
    """
    query_string = scope.get("query_string", b"").decode("utf-8", errors="ignore")
    if not query_string:
        return None
    params = parse_qs(query_string)
    tokens = params.get("token", [])
    return tokens[0] if tokens else None


def authenticate_ws_token(token_str):
    """
    Validate a JWT access token and return the authenticated User.

    Uses the SAME signing key, algorithm, and user_id claim configured
    in NINJA_JWT settings — ensures consistency with tokens emitted
    by the /auth/login endpoint (RefreshToken.for_user).

    Returns:
        User instance if valid and user exists, None otherwise.
    """
    try:
        signing_key = settings.NINJA_JWT.get("SIGNING_KEY", settings.SECRET_KEY)
        algorithm = settings.NINJA_JWT.get("ALGORITHM", "HS256")
        user_id_claim = settings.NINJA_JWT.get("USER_ID_CLAIM", "user_id")

        payload = jwt.decode(
            token_str,
            signing_key,
            algorithms=[algorithm],
        )

        user_id = payload.get(user_id_claim)
        if user_id is None:
            logger.warning("WS JWT missing '%s' claim", user_id_claim)
            return None

        return User.objects.get(id=user_id)

    except jwt.ExpiredSignatureError:
        logger.warning("WS JWT token expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning("WS JWT invalid: %s", exc)
        return None
    except User.DoesNotExist:
        logger.warning("WS JWT valid but user_id=%s not found", user_id)
        return None
