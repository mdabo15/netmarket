"""Endpoints for the buyer's saved addresses / pickup points."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.addresses import service
from app.addresses.schemas import AddressCreate, AddressRead, AddressUpdate
from app.common.schemas import Message
from app.core.deps import get_current_user, get_db
from app.users.models import User

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.post("", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
async def create_address(
    payload: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AddressRead:
    return await service.create_address(db, current_user, payload)


@router.get("", response_model=list[AddressRead])
async def list_my_addresses(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[AddressRead]:
    return await service.list_my_addresses(db, current_user)


@router.patch("/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: uuid.UUID,
    payload: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AddressRead:
    return await service.update_address(db, current_user, address_id, payload)


@router.delete("/{address_id}", response_model=Message)
async def delete_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Message:
    await service.delete_address(db, current_user, address_id)
    return Message(detail="Adresse supprimée.")
