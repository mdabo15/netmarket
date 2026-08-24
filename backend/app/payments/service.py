"""Payment orchestration: pick a provider by the order's payment method, persist the result."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models import Order
from app.payments import repository
from app.payments.models import PaymentStatus
from app.payments.provider import get_provider


async def create_payment_for_order(db: AsyncSession, order: Order) -> None:
    provider = get_provider(order.payment_method)
    status, provider_reference = await provider.initiate(order)
    await repository.create(
        db, order_id=order.id, method=order.payment_method, status=status, provider_reference=provider_reference
    )


async def _set_status(db: AsyncSession, order_id: uuid.UUID, status: PaymentStatus) -> None:
    payment = await repository.get_by_order_id(db, order_id)
    if payment is not None:
        payment.status = status


async def mark_paid(db: AsyncSession, order_id: uuid.UUID) -> None:
    """Called once every sub-order of an order reaches "delivered" — for cash on
    delivery, that's the moment the money actually changed hands."""
    await _set_status(db, order_id, PaymentStatus.PAID)


async def mark_cancelled(db: AsyncSession, order_id: uuid.UUID) -> None:
    await _set_status(db, order_id, PaymentStatus.CANCELLED)
