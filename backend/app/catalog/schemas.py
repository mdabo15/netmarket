"""Pydantic schemas: categories, products, and product search filters."""

import uuid
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Literal

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app.catalog.models import ProductStatus


class ProductSort(StrEnum):
    RECENT = "recent"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


StockLevel = Literal["out", "low"]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: uuid.UUID | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None


class ProductCreate(BaseModel):
    category_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: int = Field(ge=0, description="Prix en GNF, montant entier")
    stock: int = Field(default=0, ge=0)
    images: list[str] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    images: list[str] | None = None
    status: ProductStatus | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: uuid.UUID
    vendor_shop_name: str
    category_id: uuid.UUID
    name: str
    description: str | None
    price: int
    stock: int
    images: list[str]
    status: ProductStatus
    average_rating: float | None = None
    review_count: int = 0
    # Estimation générique (zone acheteur inconnue à ce stade — voir
    # app/common/delivery_estimate.py) ; une estimation précise n'apparaît
    # qu'une fois la commande passée, une fois la zone de livraison connue.
    estimated_delivery_min: date | None = None
    estimated_delivery_max: date | None = None


@dataclass
class ProductFilters:
    category_id: uuid.UUID | None
    min_price: int | None
    max_price: int | None
    in_stock: bool | None
    q: str | None
    sort: ProductSort = ProductSort.RECENT
    # Not settable from the public query params below — only constructed
    # internally by catalog/service.py::list_my_products, for the vendor's
    # own product list (which also needs non-active products, unlike the
    # public catalog).
    vendor_id: uuid.UUID | None = None
    # Vendor-only filters (see my_product_filters below) — a vendor narrowing
    # their own "Mes produits" list, never exposed on the public catalog.
    status: ProductStatus | None = None
    stock_level: StockLevel | None = None


def product_filters(
    category_id: uuid.UUID | None = Query(default=None, description="Filtrer par catégorie"),
    min_price: int | None = Query(default=None, ge=0, description="Prix minimum en GNF"),
    max_price: int | None = Query(default=None, ge=0, description="Prix maximum en GNF"),
    in_stock: bool | None = Query(default=None, description="Uniquement les produits disponibles en stock"),
    q: str | None = Query(default=None, min_length=1, max_length=100, description="Recherche par nom de produit"),
    sort: ProductSort = Query(default=ProductSort.RECENT, description="Tri des résultats"),
) -> ProductFilters:
    return ProductFilters(
        category_id=category_id, min_price=min_price, max_price=max_price, in_stock=in_stock, q=q, sort=sort
    )


def my_product_filters(
    category_id: uuid.UUID | None = Query(default=None, description="Filtrer par catégorie"),
    status: ProductStatus | None = Query(default=None, description="Filtrer par statut (actif/inactif)"),
    stock_level: StockLevel | None = Query(
        default=None, description="'out' = rupture de stock, 'low' = stock faible"
    ),
    sort: ProductSort = Query(default=ProductSort.RECENT, description="Tri des résultats"),
) -> ProductFilters:
    return ProductFilters(
        category_id=category_id,
        min_price=None,
        max_price=None,
        in_stock=None,
        q=None,
        sort=sort,
        status=status,
        stock_level=stock_level,
    )
