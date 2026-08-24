"""Database access for the cart, including the product/vendor join used to
render the cart grouped by vendor."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cart.models import CartItem
from app.catalog.models import Product
from app.vendors.models import Vendor


async def get_item_by_product(db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID) -> CartItem | None:
    result = await db.execute(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    )
    return result.scalar_one_or_none()


async def get_item_by_id(db: AsyncSession, item_id: uuid.UUID) -> CartItem | None:
    result = await db.execute(select(CartItem).where(CartItem.id == item_id))
    return result.scalar_one_or_none()


async def create_item(db: AsyncSession, *, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> CartItem:
    item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
    db.add(item)
    await db.flush()
    return item


async def delete_item(db: AsyncSession, item: CartItem) -> None:
    await db.delete(item)


async def clear_for_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(delete(CartItem).where(CartItem.user_id == user_id))


async def list_items_with_product_and_vendor(
    db: AsyncSession, user_id: uuid.UUID
) -> list[tuple[CartItem, Product, Vendor]]:
    stmt = (
        select(CartItem, Product, Vendor)
        .join(Product, CartItem.product_id == Product.id)
        .join(Vendor, Product.vendor_id == Vendor.id)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.created_at)
    )
    result = await db.execute(stmt)
    return list(result.all())
