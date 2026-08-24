"""Database access for reviews, including the rating aggregates the catalog displays on product cards."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.reviews.models import Review


async def get_by_product_and_user(db: AsyncSession, product_id: uuid.UUID, user_id: uuid.UUID) -> Review | None:
    result = await db.execute(select(Review).where(Review.product_id == product_id, Review.user_id == user_id))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, review_id: uuid.UUID) -> Review | None:
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()


async def delete(db: AsyncSession, review: Review) -> None:
    await db.delete(review)


async def create(
    db: AsyncSession, *, product_id: uuid.UUID, user_id: uuid.UUID, rating: int, comment: str | None
) -> Review:
    review = Review(product_id=product_id, user_id=user_id, rating=rating, comment=comment)
    db.add(review)
    await db.flush()
    return review


async def list_for_product(db: AsyncSession, product_id: uuid.UUID) -> list[Review]:
    stmt = select(Review).where(Review.product_id == product_id).order_by(Review.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def get_rating_summary(db: AsyncSession, product_id: uuid.UUID) -> tuple[float | None, int]:
    stmt = select(func.avg(Review.rating), func.count(Review.id)).where(Review.product_id == product_id)
    average, count = (await db.execute(stmt)).one()
    return (float(average) if average is not None else None, count)


async def get_rating_summary_map(
    db: AsyncSession, product_ids: list[uuid.UUID]
) -> dict[uuid.UUID, tuple[float, int]]:
    if not product_ids:
        return {}
    stmt = (
        select(Review.product_id, func.avg(Review.rating), func.count(Review.id))
        .where(Review.product_id.in_(product_ids))
        .group_by(Review.product_id)
    )
    rows = (await db.execute(stmt)).all()
    return {product_id: (float(average), count) for product_id, average, count in rows}
