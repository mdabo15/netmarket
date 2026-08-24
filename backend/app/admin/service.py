"""Compose aggregate queries into the admin dashboard payload."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import repository
from app.admin.schemas import AdminStats, TopProduct, TopVendor
from app.core.pagination import PageParams
from app.orders.models import Order, OrderStatus


async def get_stats(db: AsyncSession) -> AdminStats:
    vendor_counts = await repository.count_vendors_by_status(db)
    order_counts = await repository.count_orders_by_status(db)
    total_products = await repository.count_products(db)
    total_sales, total_commission = await repository.sum_sales_and_commission(db)
    top_products_rows = await repository.top_products(db)
    top_vendors_rows = await repository.top_vendors(db)

    return AdminStats(
        total_vendors=sum(vendor_counts.values()),
        pending_vendors=vendor_counts["pending"],
        approved_vendors=vendor_counts["approved"],
        total_products=total_products,
        total_orders=sum(order_counts.values()),
        orders_by_status=order_counts,
        total_sales=total_sales,
        total_commission=total_commission,
        top_products=[
            TopProduct(product_id=product_id, product_name=name, quantity_sold=int(qty))
            for product_id, name, qty in top_products_rows
        ],
        top_vendors=[
            TopVendor(vendor_id=vendor_id, shop_name=name, revenue=int(revenue))
            for vendor_id, name, revenue in top_vendors_rows
        ],
    )


async def list_orders(
    db: AsyncSession, params: PageParams, status_filter: OrderStatus | None
) -> tuple[list[Order], int]:
    return await repository.list_all_orders(db, params, status_filter)
