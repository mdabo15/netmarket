"""Tests for checkout (multi-vendor split), order tracking, and sub-order status transitions."""

from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import Category, Product
from app.users.models import User
from app.vendors.models import Vendor
from tests.conftest import auth_headers, make_vendor

CHECKOUT_PAYLOAD = {"delivery_address": "Kaloum, près du marché", "payment_method": "cash_on_delivery"}


async def _add_to_cart(client: AsyncClient, user: User, product: Product, quantity: int = 1) -> None:
    response = await client.post(
        "/cart/items",
        json={"product_id": str(product.id), "quantity": quantity},
        headers=auth_headers(user),
    )
    assert response.status_code == 201


async def test_checkout_splits_cart_by_vendor_and_decrements_stock(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, product: Product, category: Category
) -> None:
    _, other_vendor = await make_vendor(db_session, phone="+224620006666", shop_name="Deuxième Boutique")
    other_product = Product(vendor_id=other_vendor.id, category_id=category.id, name="Casque", price=100000, stock=5)
    db_session.add(other_product)
    await db_session.flush()

    await _add_to_cart(client, buyer_user, product, quantity=2)
    await _add_to_cart(client, buyer_user, other_product, quantity=1)

    response = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))

    assert response.status_code == 201
    order = response.json()
    assert order["total"] == product.price * 2 + other_product.price
    assert len(order["sub_orders"]) == 2
    assert order["status"] == "pending"

    cart_response = await client.get("/cart", headers=auth_headers(buyer_user))
    assert cart_response.json()["vendors"] == []

    await db_session.refresh(product)
    await db_session.refresh(other_product)
    assert product.stock == 8
    assert other_product.stock == 4


async def test_checkout_pickup_point_without_a_point_selected_is_rejected(
    client: AsyncClient, buyer_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product)

    response = await client.post(
        "/orders/checkout",
        json={
            "delivery_address": "Retrait en personne",
            "delivery_type": "pickup_point",
            "payment_method": "cash_on_delivery",
        },
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 409


async def test_checkout_freezes_delivery_estimate_for_matching_zone(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, vendor: Vendor, product: Product
) -> None:
    vendor.zone = "Kaloum"
    vendor.preparation_days = 2
    await db_session.flush()

    await _add_to_cart(client, buyer_user, product)
    response = await client.post(
        "/orders/checkout",
        json={**CHECKOUT_PAYLOAD, "delivery_zone": "Kaloum"},
        headers=auth_headers(buyer_user),
    )

    sub_order = response.json()["sub_orders"][0]
    today = date.today()
    assert sub_order["estimated_delivery_min"] == str(today + timedelta(days=2))
    assert sub_order["estimated_delivery_max"] == str(today + timedelta(days=3))


async def test_checkout_delivery_estimate_adds_a_day_for_a_different_zone(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, vendor: Vendor, product: Product
) -> None:
    vendor.zone = "Kaloum"
    vendor.preparation_days = 2
    await db_session.flush()

    await _add_to_cart(client, buyer_user, product)
    response = await client.post(
        "/orders/checkout",
        json={**CHECKOUT_PAYLOAD, "delivery_zone": "Ratoma"},
        headers=auth_headers(buyer_user),
    )

    sub_order = response.json()["sub_orders"][0]
    today = date.today()
    assert sub_order["estimated_delivery_min"] == str(today + timedelta(days=3))
    assert sub_order["estimated_delivery_max"] == str(today + timedelta(days=4))


async def test_checkout_computes_commission_from_vendor_rate(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, buyer_user: User, vendor: Vendor, product: Product
) -> None:
    await client.patch(
        f"/admin/vendors/{vendor.id}", json={"commission_rate": 10}, headers=auth_headers(admin_user)
    )

    await _add_to_cart(client, buyer_user, product, quantity=1)
    response = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))

    sub_order = response.json()["sub_orders"][0]
    assert sub_order["amount"] == product.price
    assert sub_order["commission"] == round(product.price * 0.10)


async def test_checkout_defaults_to_home_delivery(client: AsyncClient, buyer_user: User, product: Product) -> None:
    await _add_to_cart(client, buyer_user, product)

    response = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))

    assert response.json()["delivery_type"] == "home_delivery"


async def test_checkout_accepts_pickup_point_delivery_type(
    client: AsyncClient, buyer_user: User, product: Product, pickup_point
) -> None:
    await _add_to_cart(client, buyer_user, product)

    response = await client.post(
        "/orders/checkout",
        json={**CHECKOUT_PAYLOAD, "delivery_type": "pickup_point", "pickup_point_id": str(pickup_point.id)},
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 201
    assert response.json()["delivery_type"] == "pickup_point"


async def test_checkout_pickup_point_without_id_fails(
    client: AsyncClient, buyer_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product)

    response = await client.post(
        "/orders/checkout",
        json={**CHECKOUT_PAYLOAD, "delivery_type": "pickup_point"},
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 409


async def test_checkout_empty_cart_fails(client: AsyncClient, buyer_user: User) -> None:
    response = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))

    assert response.status_code == 409


async def test_checkout_insufficient_stock_fails_and_does_not_mutate_stock(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product, quantity=product.stock + 1)

    response = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))

    assert response.status_code == 409
    await db_session.refresh(product)
    assert product.stock == 10


async def test_checkout_rejects_unsupported_payment_method(client: AsyncClient, buyer_user: User, product: Product) -> None:
    await _add_to_cart(client, buyer_user, product)

    response = await client.post(
        "/orders/checkout",
        json={"delivery_address": "Kaloum", "payment_method": "orange_money"},
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 422


async def test_buyer_cannot_access_another_buyers_order(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product)
    checkout_response = await client.post(
        "/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user)
    )
    order_id = checkout_response.json()["id"]

    other_buyer, _ = await make_vendor(db_session, phone="+224620005555", shop_name="Sans Rapport")
    response = await client.get(f"/orders/{order_id}", headers=auth_headers(other_buyer))

    assert response.status_code == 404


async def test_vendor_status_transitions_and_order_status_sync(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, vendor_user: User, product: Product, category: Category
) -> None:
    _, other_vendor = await make_vendor(db_session, phone="+224620004444", shop_name="Deuxième Boutique")
    other_product = Product(vendor_id=other_vendor.id, category_id=category.id, name="Casque", price=100000, stock=5)
    db_session.add(other_product)
    await db_session.flush()

    await _add_to_cart(client, buyer_user, product)
    await _add_to_cart(client, buyer_user, other_product)
    checkout_response = await client.post(
        "/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user)
    )
    order = checkout_response.json()
    my_sub_order = next(so for so in order["sub_orders"] if so["shop_name"] == "Boutique Test")

    vendor_headers = auth_headers(vendor_user)
    confirm_response = await client.patch(
        f"/orders/sub-orders/{my_sub_order['id']}/status", json={"status": "confirmed"}, headers=vendor_headers
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "confirmed"

    # L'autre sous-commande est toujours "pending" : le statut global de la commande reste "pending".
    order_response = await client.get(f"/orders/{order['id']}", headers=auth_headers(buyer_user))
    assert order_response.json()["status"] == "pending"

    invalid_response = await client.patch(
        f"/orders/sub-orders/{my_sub_order['id']}/status", json={"status": "shipped"}, headers=vendor_headers
    )
    assert invalid_response.status_code == 409


async def test_other_vendor_cannot_update_foreign_sub_order(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product)
    checkout_response = await client.post(
        "/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user)
    )
    sub_order_id = checkout_response.json()["sub_orders"][0]["id"]

    other_vendor_user, _ = await make_vendor(db_session, phone="+224620003333", shop_name="Autre Boutique")
    response = await client.patch(
        f"/orders/sub-orders/{sub_order_id}/status",
        json={"status": "confirmed"},
        headers=auth_headers(other_vendor_user),
    )

    assert response.status_code == 403


async def test_buyer_can_cancel_pending_order_and_stock_is_restored(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product, quantity=3)
    checkout_response = await client.post(
        "/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user)
    )
    order_id = checkout_response.json()["id"]

    response = await client.post(f"/orders/{order_id}/cancel", headers=auth_headers(buyer_user))

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    await db_session.refresh(product)
    assert product.stock == 10


async def test_buyer_cannot_cancel_after_vendor_confirms(
    client: AsyncClient, buyer_user: User, vendor_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product)
    checkout_response = await client.post(
        "/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user)
    )
    order = checkout_response.json()
    sub_order_id = order["sub_orders"][0]["id"]

    await client.patch(
        f"/orders/sub-orders/{sub_order_id}/status", json={"status": "confirmed"}, headers=auth_headers(vendor_user)
    )

    response = await client.post(f"/orders/{order['id']}/cancel", headers=auth_headers(buyer_user))

    assert response.status_code == 409
