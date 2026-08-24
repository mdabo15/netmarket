"""Tests for the cart: add/update/remove, vendor grouping, ownership."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import Category, Product
from app.users.models import User
from tests.conftest import auth_headers, make_vendor


async def test_add_item_creates_entry_grouped_by_vendor(
    client: AsyncClient, buyer_user: User, product: Product
) -> None:
    response = await client.post(
        "/cart/items", json={"product_id": str(product.id), "quantity": 2}, headers=auth_headers(buyer_user)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["total"] == product.price * 2
    assert len(body["vendors"]) == 1
    assert body["vendors"][0]["items"][0]["quantity"] == 2


async def test_add_same_product_twice_increments_quantity(
    client: AsyncClient, buyer_user: User, product: Product
) -> None:
    headers = auth_headers(buyer_user)
    await client.post("/cart/items", json={"product_id": str(product.id), "quantity": 1}, headers=headers)

    response = await client.post("/cart/items", json={"product_id": str(product.id), "quantity": 2}, headers=headers)

    body = response.json()
    assert body["vendors"][0]["items"][0]["quantity"] == 3


async def test_update_and_remove_item(client: AsyncClient, buyer_user: User, product: Product) -> None:
    headers = auth_headers(buyer_user)
    add_response = await client.post(
        "/cart/items", json={"product_id": str(product.id), "quantity": 1}, headers=headers
    )
    item_id = add_response.json()["vendors"][0]["items"][0]["id"]

    update_response = await client.patch(f"/cart/items/{item_id}", json={"quantity": 5}, headers=headers)
    assert update_response.json()["vendors"][0]["items"][0]["quantity"] == 5

    remove_response = await client.delete(f"/cart/items/{item_id}", headers=headers)
    assert remove_response.json()["vendors"] == []


async def test_add_inactive_product_fails(client: AsyncClient, vendor_user: User, buyer_user: User, product: Product) -> None:
    await client.patch(
        f"/products/{product.id}", json={"status": "inactive"}, headers=auth_headers(vendor_user)
    )

    response = await client.post(
        "/cart/items", json={"product_id": str(product.id), "quantity": 1}, headers=auth_headers(buyer_user)
    )

    assert response.status_code == 409


async def test_cart_item_ownership_is_enforced(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, product: Product
) -> None:
    add_response = await client.post(
        "/cart/items", json={"product_id": str(product.id), "quantity": 1}, headers=auth_headers(buyer_user)
    )
    item_id = add_response.json()["vendors"][0]["items"][0]["id"]

    other_user, _ = await make_vendor(db_session, phone="+224620008888", shop_name="Autre")
    response = await client.patch(f"/cart/items/{item_id}", json={"quantity": 2}, headers=auth_headers(other_user))

    assert response.status_code == 403


async def test_cart_groups_multiple_vendors(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, product: Product, category: Category
) -> None:
    _, other_vendor = await make_vendor(db_session, phone="+224620007777", shop_name="Deuxième Boutique")
    other_product = Product(vendor_id=other_vendor.id, category_id=category.id, name="Casque", price=100000, stock=5)
    db_session.add(other_product)
    await db_session.flush()

    headers = auth_headers(buyer_user)
    await client.post("/cart/items", json={"product_id": str(product.id), "quantity": 1}, headers=headers)
    response = await client.post(
        "/cart/items", json={"product_id": str(other_product.id), "quantity": 1}, headers=headers
    )

    assert len(response.json()["vendors"]) == 2
