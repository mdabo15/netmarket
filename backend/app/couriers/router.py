"""Courier ("livreur") endpoints: self-registration, public directory (for
vendors picking who delivers their sub-order), and admin validation.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.couriers import service
from app.couriers.models import CourierStatus
from app.couriers.schemas import CourierAdminCreate, CourierAdminUpdate, CourierRead, CourierRegister
from app.users.models import User, UserRole

router = APIRouter(prefix="/couriers", tags=["couriers"])
admin_router = APIRouter(
    prefix="/admin/couriers", tags=["admin"], dependencies=[Depends(require_role(UserRole.ADMIN))]
)


@router.post("/me", response_model=CourierRead, status_code=status.HTTP_201_CREATED)
async def register_courier(
    payload: CourierRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourierRead:
    return await service.register_courier(db, current_user, payload)


@router.get("/me", response_model=CourierRead)
async def get_my_courier(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> CourierRead:
    return await service.get_my_courier(db, current_user)


@router.get("", response_model=list[CourierRead])
async def list_couriers(db: AsyncSession = Depends(get_db)) -> list[CourierRead]:
    return await service.list_public_couriers(db)


@admin_router.post("", response_model=CourierRead, status_code=status.HTTP_201_CREATED)
async def admin_create_courier(payload: CourierAdminCreate, db: AsyncSession = Depends(get_db)) -> CourierRead:
    return await service.admin_create_courier(db, payload)


@admin_router.get("", response_model=list[CourierRead])
async def admin_list_couriers(
    status_filter: CourierStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[CourierRead]:
    return await service.admin_list_couriers(db, status_filter)


@admin_router.patch("/{courier_id}", response_model=CourierRead)
async def admin_update_courier(
    courier_id: uuid.UUID, payload: CourierAdminUpdate, db: AsyncSession = Depends(get_db)
) -> CourierRead:
    return await service.admin_update_courier(db, courier_id, payload)
