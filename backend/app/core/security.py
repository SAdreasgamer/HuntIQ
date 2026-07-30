"""
HuntIQ — Security & JWT Authentication Module.

Password hashing via native bcrypt and JWT token generation/verification via PyJWT.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config.settings import get_settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.logging import get_logger

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """Hash a plain text password using native bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]  # Truncate to bcrypt limit if needed
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored bcrypt hash."""
    pw_bytes = plain_password.encode("utf-8")[:72]
    hash_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: Token subject (typically User ID).
        expires_delta: Optional custom expiry duration.
        extra_claims: Optional dictionary of additional claims.

    Returns:
        Encoded JWT token string.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.security.access_token_expire_minutes)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
        **(extra_claims or {}),
    }

    secret_key = settings.security.secret_key.get_secret_value()
    encoded_jwt = jwt.encode(payload, secret_key, algorithm=settings.security.algorithm)
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT refresh token with longer expiry."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.security.refresh_token_expire_days)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }

    secret_key = settings.security.secret_key.get_secret_value()
    return jwt.encode(payload, secret_key, algorithm=settings.security.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT string.

    Returns:
        Decoded payload dictionary.

    Raises:
        TokenExpiredError: If token expiration (exp) is in the past.
        InvalidTokenError: If signature or token format is invalid.
    """
    settings = get_settings()
    secret_key = settings.security.secret_key.get_secret_value()

    try:
        payload = jwt.decode(token, secret_key, algorithms=[settings.security.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError:
        raise InvalidTokenError()
