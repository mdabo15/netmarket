"""Business logic for admin-managed pickup points."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.pickup_points import repository
from app.pickup_points.models import PickupPoint
from app.pickup_points.schemas import PickupPointCreate, PickupPointUpdate


async def create_point(db: AsyncSession, data: PickupPointCreate) -> PickupPoint:
    point = await repository.create(db, **data.model_dump())
    await db.commit()
    await db.refresh(point)
    return point


async def list_public_points(db: AsyncSession) -> list[PickupPoint]:
    return await repository.list_active(db)


async def admin_list_points(db: AsyncSession) -> list[PickupPoint]:
    return await repository.list_all(db)


async def update_point(db: AsyncSession, point_id: uuid.UUID, data: PickupPointUpdate) -> PickupPoint:
    point = await repository.get_by_id(db, point_id)
    if point is None:
        raise NotFoundError("Point de retrait introuvable.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(point, field, value)

    await db.commit()
    await db.refresh(point)
    return point


async def delete_point(db: AsyncSession, point_id: uuid.UUID) -> None:
    point = await repository.get_by_id(db, point_id)
    if point is None:
        raise NotFoundError("Point de retrait introuvable.")
    await repository.delete(db, point)
    await db.commit()
