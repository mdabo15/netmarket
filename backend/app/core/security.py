"""Password hashing (Argon2) and JWT access/refresh token handling."""

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()
_hasher = PasswordHasher()


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    DELIVERY = "delivery"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta, extra_claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str) -> str:
    return _create_token(
        subject,
        TokenType.ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"role": role},
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(subject, TokenType.REFRESH, timedelta(days=settings.refresh_token_expire_days))


def create_delivery_token(sub_order_id: str) -> str:
    """Signed token embedded in the buyer's delivery QR code.

    60 days comfortably outlives any realistic shipped→delivered window
    while still being bounded (a signed token has no other expiry/revocation
    mechanism — see app/orders/service.py::confirm_delivery_by_token, which
    also re-checks the sub-order is still "shipped" before honoring it).
    """
    return _create_token(sub_order_id, TokenType.DELIVERY, timedelta(days=60))


class InvalidTokenError(Exception):
    """Raised when a JWT is missing, malformed, expired or has the wrong type."""


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError

    return payload
