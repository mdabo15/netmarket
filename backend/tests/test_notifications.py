"""Tests for order notifications: the in-app feed (persisted + listed via
/notifications) and the buyer email sent on status changes. send_email
itself (SMTP over the network) is stubbed out — these tests check the
trigger logic, not mailpit delivery."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import Product
from app.couriers.models import Courier
from app.users.models import User
from tests.conftest import auth_headers

CHECKOUT_PAYLOAD = {"delivery_address": "Kaloum, près du marché", "payment_method": "cash_on_delivery"}


async def _checkout(client: AsyncClient, buyer: User, product: Product) -> str:
    await client.post(
        "/cart/items", json={"product_id": str(product.id), "quantity": 1}, headers=auth_headers(buyer)
    )
    response = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer))
    return response.json()["sub_orders"][0]["id"]


async def test_status_change_emails_buyer_when_email_is_set(
    client: AsyncClient,
    db_session: AsyncSession,
    buyer_user: User,
    vendor_user: User,
    product: Product,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buyer_user.email = "acheteur@test.gn"
    await db_session.flush()

    calls: list[tuple[str, str, str]] = []

    async def fake_send_email(to: str, subject: str, body: str) -> None:
        calls.append((to, subject, body))

    monkeypatch.setattr("app.notifications.service.send_email", fake_send_email)

    sub_order_id = await _checkout(client, buyer_user, product)
    response = await client.patch(
        f"/orders/sub-orders/{sub_order_id}/status", json={"status": "confirmed"}, headers=auth_headers(vendor_user)
    )

    assert response.status_code == 200
    assert len(calls) == 1
    to, subject, body = calls[0]
    assert to == "acheteur@test.gn"
    assert "confirmée" in subject
    assert "Boutique Test" in body


async def test_status_change_skips_email_when_buyer_has_no_email(
    client: AsyncClient,
    buyer_user: User,
    vendor_user: User,
    product: Product,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert buyer_user.email is None

    calls: list[tuple[str, str, str]] = []

    async def fake_send_email(to: str, subject: str, body: str) -> None:
        calls.append((to, subject, body))

    monkeypatch.setattr("app.notifications.service.send_email", fake_send_email)

    sub_order_id = await _checkout(client, buyer_user, product)
    response = await client.patch(
        f"/orders/sub-orders/{sub_order_id}/status", json={"status": "confirmed"}, headers=auth_headers(vendor_user)
    )

    assert response.status_code == 200
    assert calls == []


async def test_checkout_notifies_vendor_in_app(
    client: AsyncClient, buyer_user: User, vendor_user: User, product: Product
) -> None:
    await client.post("/cart/items", json={"product_id": str(product.id), "quantity": 2}, headers=auth_headers(buyer_user))
    checkout = await client.post("/orders/checkout", json=CHECKOUT_PAYLOAD, headers=auth_headers(buyer_user))
    order_id = checkout.json()["id"]

    response = await client.get("/notifications", headers=auth_headers(vendor_user))

    assert response.status_code == 200
    body = response.json()
    assert body["unread_count"] == 1
    assert len(body["items"]) == 1
    notification = body["items"][0]
    assert notification["type"] == "order_received"
    assert notification["order_id"] == order_id
    assert notification["read_at"] is None
    assert "Boutique Test" in notification["body"]

    # L'acheteur, lui, n'a rien reçu à ce stade (rien ne s'est encore passé
    # côté vendeur) — la commande vient d'être passée, pas encore de statut.
    buyer_notifications = await client.get("/notifications", headers=auth_headers(buyer_user))
    assert buyer_notifications.json()["unread_count"] == 0


async def test_status_change_notifies_buyer_in_app(
    client: AsyncClient, buyer_user: User, vendor_user: User, product: Product
) -> None:
    sub_order_id = await _checkout(client, buyer_user, product)
    await client.patch(
        f"/orders/sub-orders/{sub_order_id}/status", json={"status": "confirmed"}, headers=auth_headers(vendor_user)
    )

    response = await client.get("/notifications", headers=auth_headers(buyer_user))

    assert response.status_code == 200
    body = response.json()
    assert body["unread_count"] == 1
    notification = body["items"][0]
    assert notification["type"] == "order_status_changed"
    assert "confirmée" in notification["title"]


async def test_mark_notification_read(client: AsyncClient, buyer_user: User, vendor_user: User, product: Product) -> None:
    sub_order_id = await _checkout(client, buyer_user, product)
    await client.patch(
        f"/orders/sub-orders/{sub_order_id}/status", json={"status": "confirmed"}, headers=auth_headers(vendor_user)
    )
    notification_id = (await client.get("/notifications", headers=auth_headers(buyer_user))).json()["items"][0]["id"]

    response = await client.patch(f"/notifications/{notification_id}/read", headers=auth_headers(buyer_user))
    assert response.status_code == 200
    assert response.json()["read_at"] is not None

    listing = await client.get("/notifications", headers=auth_headers(buyer_user))
    assert listing.json()["unread_count"] == 0


async def test_cannot_mark_another_users_notification_read(
    client: AsyncClient, buyer_user: User, vendor_user: User, product: Product
) -> None:
    sub_order_id = await _checkout(client, buyer_user, product)
    await client.patch(
        f"/orders/sub-orders/{sub_order_id}/status", json={"status": "confirmed"}, headers=auth_headers(vendor_user)
    )
    notification_id = (await client.get("/notifications", headers=auth_headers(buyer_user))).json()["items"][0]["id"]

    response = await client.patch(f"/notifications/{notification_id}/read", headers=auth_headers(vendor_user))
    assert response.status_code == 404


async def test_mark_all_read(
    client: AsyncClient, buyer_user: User, vendor_user: User, product: Product, courier: Courier
) -> None:
    sub_order_id = await _checkout(client, buyer_user, product)
    await client.patch(
        f"/orders/sub-orders/{sub_order_id}/courier",
        json={"courier_id": str(courier.id)},
        headers=auth_headers(vendor_user),
    )
    for target_status in ("confirmed", "preparing", "shipped"):
        await client.patch(
            f"/orders/sub-orders/{sub_order_id}/status",
            json={"status": target_status},
            headers=auth_headers(vendor_user),
        )
    assert (await client.get("/notifications", headers=auth_headers(buyer_user))).json()["unread_count"] == 3

    response = await client.post("/notifications/read-all", headers=auth_headers(buyer_user))
    assert response.status_code == 200

    assert (await client.get("/notifications", headers=auth_headers(buyer_user))).json()["unread_count"] == 0
