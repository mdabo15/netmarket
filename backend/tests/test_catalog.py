"""Tests for category/product CRUD, pagination and filters."""

from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import Category
from app.users.models import User, UserRole
from app.vendors.models import Vendor, VendorStatus
from tests.conftest import auth_headers, make_user


async def test_create_and_list_categories(client: AsyncClient, admin_user: User) -> None:
    create_response = await client.post("/categories", json={"name": "Mode"}, headers=auth_headers(admin_user))
    assert create_response.status_code == 201

    list_response = await client.get("/categories")
    assert list_response.status_code == 200
    assert any(c["name"] == "Mode" for c in list_response.json())


async def test_create_product_requires_vendor_role(
    client: AsyncClient, buyer_user: User, category: Category
) -> None:
    response = await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Téléphone", "price": 500000, "stock": 10},
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 403


async def test_create_product_requires_approved_vendor(
    client: AsyncClient, unapproved_vendor_user: User, category: Category
) -> None:
    response = await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Téléphone", "price": 500000, "stock": 10},
        headers=auth_headers(unapproved_vendor_user),
    )

    assert response.status_code == 403
    assert "validée" in response.json()["detail"]


async def test_vendor_can_create_and_read_product(
    client: AsyncClient, vendor_user: User, category: Category
) -> None:
    response = await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Téléphone", "price": 500000, "stock": 10},
        headers=auth_headers(vendor_user),
    )

    assert response.status_code == 201
    product = response.json()
    assert product["price"] == 500000
    assert product["status"] == "active"

    get_response = await client.get(f"/products/{product['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Téléphone"


async def test_product_filters_price_and_stock(
    client: AsyncClient, vendor_user: User, category: Category
) -> None:
    headers = auth_headers(vendor_user)
    await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Casque", "price": 100000, "stock": 0},
        headers=headers,
    )
    await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Ordinateur", "price": 2000000, "stock": 5},
        headers=headers,
    )

    response = await client.get("/products", params={"min_price": 500000, "in_stock": True})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Ordinateur"


async def test_product_pagination(client: AsyncClient, vendor_user: User, category: Category) -> None:
    headers = auth_headers(vendor_user)
    for i in range(3):
        await client.post(
            "/products",
            json={"category_id": str(category.id), "name": f"Produit {i}", "price": 1000, "stock": 1},
            headers=headers,
        )

    response = await client.get("/products", params={"page": 1, "page_size": 2})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["pages"] == 2


async def test_vendor_cannot_update_another_vendors_product(
    client: AsyncClient, db_session: AsyncSession, vendor_user: User, category: Category
) -> None:
    other_user = await make_user(db_session, phone="+224620009999", role=UserRole.VENDOR)
    other_vendor = Vendor(user_id=other_user.id, shop_name="Autre Boutique", status=VendorStatus.APPROVED)
    db_session.add(other_vendor)
    await db_session.flush()

    create_response = await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Produit", "price": 1000, "stock": 1},
        headers=auth_headers(vendor_user),
    )
    product_id = create_response.json()["id"]

    response = await client.patch(
        f"/products/{product_id}", json={"price": 2000}, headers=auth_headers(other_user)
    )

    assert response.status_code == 403


async def test_product_sort_by_price(client: AsyncClient, vendor_user: User, category: Category) -> None:
    headers = auth_headers(vendor_user)
    await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Cher", "price": 900000, "stock": 1},
        headers=headers,
    )
    await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Pas cher", "price": 10000, "stock": 1},
        headers=headers,
    )

    response = await client.get("/products", params={"sort": "price_asc"})

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["items"]]
    assert names == ["Pas cher", "Cher"]


async def test_my_products_filters_by_category_status_and_stock_level(
    client: AsyncClient, vendor_user: User, category: Category, db_session: AsyncSession
) -> None:
    headers = auth_headers(vendor_user)
    other_category = Category(name="Autre")
    db_session.add(other_category)
    await db_session.flush()

    await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Rupture", "price": 1000, "stock": 0},
        headers=headers,
    )
    faible = await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Faible", "price": 1000, "stock": 2},
        headers=headers,
    )
    await client.post(
        "/products",
        json={"category_id": str(other_category.id), "name": "Autre categorie", "price": 1000, "stock": 20},
        headers=headers,
    )
    inactive_id = faible.json()["id"]
    await client.patch(f"/products/{inactive_id}", json={"status": "inactive"}, headers=headers)

    by_category = await client.get("/products/me", params={"category_id": str(category.id)}, headers=headers)
    assert {p["name"] for p in by_category.json()["items"]} == {"Rupture", "Faible"}

    out_of_stock = await client.get("/products/me", params={"stock_level": "out"}, headers=headers)
    assert [p["name"] for p in out_of_stock.json()["items"]] == ["Rupture"]

    inactive_only = await client.get("/products/me", params={"status": "inactive"}, headers=headers)
    assert [p["name"] for p in inactive_only.json()["items"]] == ["Faible"]


async def test_product_read_exposes_generic_delivery_estimate(
    client: AsyncClient, db_session: AsyncSession, vendor_user: User, vendor: Vendor, category: Category
) -> None:
    vendor.preparation_days = 3
    await db_session.flush()

    create_response = await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Produit", "price": 1000, "stock": 1},
        headers=auth_headers(vendor_user),
    )
    product_id = create_response.json()["id"]

    response = await client.get(f"/products/{product_id}")

    today = date.today()
    body = response.json()
    # Zone acheteur inconnue sur le catalogue public : hypothèse "zone
    # différente" par défaut (voir app/catalog/service.py::_attach_delivery_estimate).
    assert body["estimated_delivery_min"] == str(today + timedelta(days=4))
    assert body["estimated_delivery_max"] == str(today + timedelta(days=5))


async def test_admin_can_delete_any_product(
    client: AsyncClient, vendor_user: User, admin_user: User, category: Category
) -> None:
    create_response = await client.post(
        "/products",
        json={"category_id": str(category.id), "name": "Produit", "price": 1000, "stock": 1},
        headers=auth_headers(vendor_user),
    )
    product_id = create_response.json()["id"]

    response = await client.delete(f"/products/{product_id}", headers=auth_headers(admin_user))

    assert response.status_code == 200
    assert (await client.get(f"/products/{product_id}")).status_code == 404
