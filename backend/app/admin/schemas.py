"""Admin dashboard schemas: platform-wide statistics."""

import uuid

from pydantic import BaseModel


class TopProduct(BaseModel):
    product_id: uuid.UUID
    product_name: str
    quantity_sold: int


class TopVendor(BaseModel):
    vendor_id: uuid.UUID
    shop_name: str
    revenue: int


class AdminStats(BaseModel):
    total_vendors: int
    pending_vendors: int
    approved_vendors: int
    total_products: int
    total_orders: int
    orders_by_status: dict[str, int]
    # Ventes/commission comptées sur les sous-commandes livrées uniquement :
    # en paiement à la livraison, l'argent ne change vraiment de main qu'à ce moment-là.
    total_sales: int
    total_commission: int
    top_products: list[TopProduct]
    top_vendors: list[TopVendor]
