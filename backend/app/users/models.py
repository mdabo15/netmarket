"""User ORM model, role enum, and email verification codes."""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class UserRole(StrEnum):
    BUYER = "buyer"
    VENDOR = "vendor"
    COURIER = "courier"
    PICKUP_POINT_MANAGER = "pickup_point_manager"
    ADMIN = "admin"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", values_callable=lambda enum: [e.value for e in enum]),
        default=UserRole.BUYER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Only meaningful once `email` is set. Currently gated behind vendor
    # onboarding (see app/vendors/service.py) — buyers can leave email unset
    # entirely, so this stays False and unused for them.
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EmailVerificationCode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One active code per user — a new send (register/resend) replaces it.

    The code itself is short (4-5 digits, ~100k possibilities), so `attempts`
    caps guesses and `expires_at` bounds the window; both matter more here
    than they would for a long random token.
    """

    __tablename__ = "email_verification_codes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
