"""Registration, login and token refresh business logic.

Self-registration always creates a buyer account. Promoting a user to vendor
or admin is handled by dedicated flows (vendor onboarding + admin validation),
not exposed here, so a client can never grant itself elevated privileges.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, RegisterRequest, TokenPair
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.users import repository
from app.users.models import User, UserRole

INVALID_CREDENTIALS_MESSAGE = "Numéro de téléphone ou mot de passe incorrect."


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    if await repository.get_by_phone(db, data.phone) is not None:
        raise ConflictError("Ce numéro de téléphone est déjà utilisé.")
    if data.email and await repository.get_by_email(db, data.email) is not None:
        raise ConflictError("Cet email est déjà utilisé.")

    user = await repository.create(
        db,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=UserRole.BUYER,
        email=data.email,
    )
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, data: LoginRequest) -> User:
    user = await repository.get_by_phone(db, data.phone)
    if user is None or not verify_password(data.password, user.password_hash):
        raise UnauthorizedError(INVALID_CREDENTIALS_MESSAGE)
    if not user.is_active:
        raise UnauthorizedError("Ce compte a été désactivé.")
    return user


def issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
    )


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenPair:
    try:
        payload = decode_token(refresh_token, TokenType.REFRESH)
        user_id = uuid.UUID(payload["sub"])
    except (InvalidTokenError, ValueError) as exc:
        raise UnauthorizedError("Jeton de rafraîchissement invalide ou expiré, veuillez vous reconnecter.") from exc

    user = await repository.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Compte introuvable ou désactivé.")

    return issue_tokens(user)
