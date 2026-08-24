"""Product review endpoints, nested under /products/{product_id}/reviews."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.reviews import service
from app.reviews.schemas import ReviewCreate, ReviewRead
from app.users.models import User

router = APIRouter(prefix="/products/{product_id}/reviews", tags=["reviews"])


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    product_id: uuid.UUID,
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewRead:
    return await service.create_review(db, current_user.id, product_id, payload)


@router.get("", response_model=list[ReviewRead])
async def list_reviews(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[ReviewRead]:
    return await service.list_reviews_for_product(db, product_id)
