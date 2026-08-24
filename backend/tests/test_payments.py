"""Tests for the payments module: created at checkout, settled on delivery/cancellation."""

from httpx import AsyncClient

from app.catalog.models import Product
from app.couriers.models import Courier
from app.users.models import User
from tests.conftest import auth_headers

CHECKOUT_PAYLOAD = {"delivery_address": "Kaloum, près du marché", "payment_method": "cash_on_delivery"}


async def _add_to_cart(client: AsyncClient, user: User, product: Product, quantity: int = 1) -> None:
    response = await client.post(
        "/cart/items", json={"product_id": str(product.id), "quantity": quantity}, headers=auth_headers(user)
    )
    assert response.status_code == 201


async def test_checkout_creates_pending_cash_on_delivery_payment(
    client: AsyncClient, buyer_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product)
    response = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))

    order = response.json()
    assert order["payment_method"] == "cash_on_delivery"
    assert order["payment_status"] == "pending"


async def test_payment_marked_paid_once_order_fully_delivered(
    client: AsyncClient, buyer_user: User, vendor_user: User, courier_user: User, product: Product, courier: Courier
) -> None:
    await _add_to_cart(client, buyer_user, product)
    checkout_response = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))
    order = checkout_response.json()
    sub_order_id = order["sub_orders"][0]["id"]
    vendor_headers = auth_headers(vendor_user)
    await client.patch(
        f"/orders/sub-orders/{sub_order_id}/courier", json={"courier_id": str(courier.id)}, headers=vendor_headers
    )

    for target_status in ("confirmed", "preparing", "shipped"):
        step = await client.patch(
            f"/orders/sub-orders/{sub_order_id}/status", json={"status": target_status}, headers=vendor_headers
        )
        assert step.status_code == 200
    # La remise finale revient au livreur, pas au vendeur.
    delivered_step = await client.patch(
        f"/orders/sub-orders/{sub_order_id}/status",
        json={"status": "delivered"},
        headers=auth_headers(courier_user),
    )
    assert delivered_step.status_code == 200

    order_response = await client.get(f"/orders/{order['id']}", headers=auth_headers(buyer_user))
    assert order_response.json()["payment_status"] == "paid"


async def test_payment_marked_cancelled_when_buyer_cancels_order(
    client: AsyncClient, buyer_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product)
    checkout_response = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))
    order_id = checkout_response.json()["id"]

    cancel_response = await client.post(f"/orders/{order_id}/cancel", headers=auth_headers(buyer_user))

    assert cancel_response.json()["payment_status"] == "cancelled"


async def test_order_list_includes_payment_status_for_each_order(
    client: AsyncClient, buyer_user: User, product: Product
) -> None:
    await _add_to_cart(client, buyer_user, product)
    await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))

    list_response = await client.get("/orders", headers=auth_headers(buyer_user))

    assert list_response.status_code == 200
    assert all(order["payment_status"] == "pending" for order in list_response.json())
