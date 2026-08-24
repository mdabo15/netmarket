"""Database access for User. Also used by the auth module (registration/login)."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import EmailVerificationCode, User, UserRole


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_phone(db: AsyncSession, phone: str) -> User | None:
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    phone: str,
    password_hash: str,
    role: UserRole,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    user = User(
        phone=phone,
        password_hash=password_hash,
        role=role,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    await db.flush()
    return user


async def get_verification_code(db: AsyncSession, user_id: uuid.UUID) -> EmailVerificationCode | None:
    result = await db.execute(select(EmailVerificationCode).where(EmailVerificationCode.user_id == user_id))
    return result.scalar_one_or_none()


async def put_verification_code(
    db: AsyncSession, user_id: uuid.UUID, *, code_hash: str, expires_at: datetime
) -> EmailVerificationCode:
    """Replace whatever code this user currently has (register, or a resend) with a fresh one."""
    existing = await get_verification_code(db, user_id)
    if existing is not None:
        await db.delete(existing)
        await db.flush()
    record = EmailVerificationCode(user_id=user_id, code_hash=code_hash, expires_at=expires_at)
    db.add(record)
    await db.flush()
    return record


async def delete_verification_code(db: AsyncSession, record: EmailVerificationCode) -> None:
    await db.delete(record)
