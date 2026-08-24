"""Database access for PickupPointManager."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.pickup_point_managers.models import PickupPointManager
from app.users.models import User


def _attach_user_fields(manager: PickupPointManager, user: User) -> PickupPointManager:
    manager.phone = user.phone
    full_name = " ".join(part for part in (user.first_name, user.last_name) if part)
    manager.full_name = full_name or None
    return manager


async def get_by_id(db: AsyncSession, manager_id: uuid.UUID) -> PickupPointManager | None:
    stmt = (
        select(PickupPointManager, User)
        .join(User, PickupPointManager.user_id == User.id)
        .where(PickupPointManager.id == manager_id)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    manager, user = row
    return _attach_user_fields(manager, user)


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> PickupPointManager | None:
    stmt = (
        select(PickupPointManager, User)
        .join(User, PickupPointManager.user_id == User.id)
        .where(PickupPointManager.user_id == user_id)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    manager, user = row
    return _attach_user_fields(manager, user)


async def create(db: AsyncSession, *, user_id: uuid.UUID, pickup_point_id: uuid.UUID) -> PickupPointManager:
    manager = PickupPointManager(user_id=user_id, pickup_point_id=pickup_point_id)
    db.add(manager)
    await db.flush()
    return manager


async def list_by_pickup_point(db: AsyncSession, pickup_point_id: uuid.UUID | None) -> list[PickupPointManager]:
    stmt = select(PickupPointManager, User).join(User, PickupPointManager.user_id == User.id)
    if pickup_point_id is not None:
        stmt = stmt.where(PickupPointManager.pickup_point_id == pickup_point_id)
    rows = (await db.execute(stmt.order_by(PickupPointManager.created_at.desc()))).all()
    return [_attach_user_fields(manager, user) for manager, user in rows]


async def delete(db: AsyncSession, manager: PickupPointManager) -> None:
    await db.delete(manager)
