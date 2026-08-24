"""Database access for saved addresses."""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.addresses.models import Address


async def create(db: AsyncSession, *, user_id: uuid.UUID, **fields) -> Address:
    address = Address(user_id=user_id, **fields)
    db.add(address)
    await db.flush()
    return address


async def get_by_id(db: AsyncSession, address_id: uuid.UUID) -> Address | None:
    result = await db.execute(select(Address).where(Address.id == address_id))
    return result.scalar_one_or_none()


async def list_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Address]:
    stmt = (
        select(Address)
        .where(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def unset_default_for_user(db: AsyncSession, user_id: uuid.UUID, *, except_id: uuid.UUID | None = None) -> None:
    stmt = update(Address).where(Address.user_id == user_id, Address.is_default.is_(True))
    if except_id is not None:
        stmt = stmt.where(Address.id != except_id)
    await db.execute(stmt.values(is_default=False))


async def delete(db: AsyncSession, address: Address) -> None:
    await db.delete(address)
