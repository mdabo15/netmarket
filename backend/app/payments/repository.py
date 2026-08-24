"""Database access for payments."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models import PaymentMethod
from app.payments.models import Payment, PaymentStatus


async def create(
    db: AsyncSession,
    *,
    order_id: uuid.UUID,
    method: PaymentMethod,
    status: PaymentStatus,
    provider_reference: str | None,
) -> Payment:
    payment = Payment(order_id=order_id, method=method, status=status, provider_reference=provider_reference)
    db.add(payment)
    await db.flush()
    return payment


async def get_by_order_id(db: AsyncSession, order_id: uuid.UUID) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    return result.scalar_one_or_none()


async def get_status_map(db: AsyncSession, order_ids: list[uuid.UUID]) -> dict[uuid.UUID, PaymentStatus]:
    if not order_ids:
        return {}
    result = await db.execute(select(Payment.order_id, Payment.status).where(Payment.order_id.in_(order_ids)))
    return {row.order_id: row.status for row in result.all()}
