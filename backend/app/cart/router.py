"""Cart endpoints: view (grouped by vendor), add, update, remove, clear.

Every mutation returns the full cart so the client can simply re-render.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cart import service
from app.cart.schemas import CartItemCreate, CartItemUpdate, CartRead
from app.core.deps import get_current_user, get_db
from app.users.models import User

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartRead)
async def get_cart(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CartRead:
    return await service.get_cart(db, current_user)


@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
async def add_item(
    payload: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartRead:
    await service.add_item(db, current_user, payload)
    return await service.get_cart(db, current_user)


@router.patch("/items/{item_id}", response_model=CartRead)
async def update_item(
    item_id: uuid.UUID,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartRead:
    await service.update_item(db, current_user, item_id, payload)
    return await service.get_cart(db, current_user)


@router.delete("/items/{item_id}", response_model=CartRead)
async def remove_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartRead:
    await service.remove_item(db, current_user, item_id)
    return await service.get_cart(db, current_user)


@router.delete("", response_model=CartRead)
async def clear_cart(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CartRead:
    await service.clear_cart(db, current_user)
    return await service.get_cart(db, current_user)
