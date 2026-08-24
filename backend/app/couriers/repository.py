"""Database access for Courier."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.couriers.models import Courier, CourierStatus
from app.users.models import User


def _attach_user_fields(courier: Courier, user: User) -> Courier:
    courier.phone = user.phone
    full_name = " ".join(part for part in (user.first_name, user.last_name) if part)
    courier.full_name = full_name or None
    return courier


async def get_by_id(db: AsyncSession, courier_id: uuid.UUID) -> Courier | None:
    stmt = select(Courier, User).join(User, Courier.user_id == User.id).where(Courier.id == courier_id)
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    courier, user = row
    return _attach_user_fields(courier, user)


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Courier | None:
    stmt = select(Courier, User).join(User, Courier.user_id == User.id).where(Courier.user_id == user_id)
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    courier, user = row
    return _attach_user_fields(courier, user)


async def create(db: AsyncSession, *, user_id: uuid.UUID, vehicle_type: str, zone: str | None) -> Courier:
    courier = Courier(user_id=user_id, vehicle_type=vehicle_type, zone=zone)
    db.add(courier)
    await db.flush()
    return courier


async def list_by_status(db: AsyncSession, status: CourierStatus | None) -> list[Courier]:
    stmt = select(Courier, User).join(User, Courier.user_id == User.id)
    if status is not None:
        stmt = stmt.where(Courier.status == status)
    rows = (await db.execute(stmt.order_by(Courier.created_at.desc()))).all()
    return [_attach_user_fields(courier, user) for courier, user in rows]
