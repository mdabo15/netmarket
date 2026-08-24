"""Review creation, gated on the buyer having actually received the product."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError
from app.orders import repository as orders_repository
from app.reviews import repository
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreate


async def create_review(db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID, data: ReviewCreate) -> Review:
    if not await orders_repository.has_delivered_product_for_user(db, user_id, product_id):
        raise ForbiddenError("Vous ne pouvez laisser un avis que sur un produit que vous avez reçu.")

    if await repository.get_by_product_and_user(db, product_id, user_id) is not None:
        raise ConflictError("Vous avez déjà laissé un avis pour ce produit.")

    review = await repository.create(
        db, product_id=product_id, user_id=user_id, rating=data.rating, comment=data.comment
    )
    await db.commit()
    await db.refresh(review)
    return review


async def list_reviews_for_product(db: AsyncSession, product_id: uuid.UUID) -> list[Review]:
    return await repository.list_for_product(db, product_id)
