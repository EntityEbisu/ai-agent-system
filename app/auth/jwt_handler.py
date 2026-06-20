"""JWT token handler — create and verify access tokens.

Uses ``pyjwt`` with HS256 signing. The secret key comes from the
``JWT_SECRET_KEY`` environment variable (must be at least 32 characters).
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(user_id: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        user_id: The subject identifier (e.g., ``"demo-user"``).
        extra_claims: Optional additional claims to include.

    Returns:
        Encoded JWT string.

    Raises:
        ValueError: If ``JWT_SECRET_KEY`` is not configured.
    """
    if not _SECRET_KEY:
        raise ValueError(
            "JWT_SECRET_KEY must be set in .env to issue tokens"
        )

    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Args:
        token: The JWT string to verify.

    Returns:
        Decoded payload dict.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is malformed or signature invalid.
    """
    if not _SECRET_KEY:
        raise ValueError(
            "JWT_SECRET_KEY must be set in .env to verify tokens"
        )
    return jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
