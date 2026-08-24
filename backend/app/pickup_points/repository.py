"""Database access for pickup points."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.pickup_points.models import PickupPoint


async def create(db: AsyncSession, **fields) -> PickupPoint:
    point = PickupPoint(**fields)
    db.add(point)
    await db.flush()
    return point


async def get_by_id(db: AsyncSession, point_id: uuid.UUID) -> PickupPoint | None:
    result = await db.execute(select(PickupPoint).where(PickupPoint.id == point_id))
    return result.scalar_one_or_none()


async def list_active(db: AsyncSession) -> list[PickupPoint]:
    stmt = select(PickupPoint).where(PickupPoint.is_active.is_(True)).order_by(PickupPoint.name)
    return list((await db.execute(stmt)).scalars().all())


async def list_all(db: AsyncSession) -> list[PickupPoint]:
    stmt = select(PickupPoint).order_by(PickupPoint.name)
    return list((await db.execute(stmt)).scalars().all())


async def delete(db: AsyncSession, point: PickupPoint) -> None:
    await db.delete(point)
