"""Tests for courier ("livreur") onboarding and admin validation."""

from httpx import AsyncClient

from app.users.models import User
from tests.conftest import auth_headers


async def test_register_courier_promotes_role_and_is_pending(client: AsyncClient, buyer_user: User) -> None:
    response = await client.post(
        "/couriers/me", json={"vehicle_type": "moto", "zone": "Kaloum"}, headers=auth_headers(buyer_user)
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"

    me = await client.get("/users/me", headers=auth_headers(buyer_user))
    assert me.json()["role"] == "courier"


async def test_register_courier_twice_fails(client: AsyncClient, buyer_user: User) -> None:
    headers = auth_headers(buyer_user)
    await client.post("/couriers/me", json={"vehicle_type": "moto"}, headers=headers)

    response = await client.post("/couriers/me", json={"vehicle_type": "taxi"}, headers=headers)

    assert response.status_code == 409


async def test_vendor_cannot_register_as_courier(client: AsyncClient, vendor_user: User) -> None:
    response = await client.post(
        "/couriers/me", json={"vehicle_type": "moto"}, headers=auth_headers(vendor_user)
    )

    assert response.status_code == 403


async def test_admin_cannot_register_as_courier(client: AsyncClient, admin_user: User) -> None:
    response = await client.post(
        "/couriers/me", json={"vehicle_type": "moto"}, headers=auth_headers(admin_user)
    )

    assert response.status_code == 403


async def test_public_listing_only_shows_approved_couriers(
    client: AsyncClient, buyer_user: User, admin_user: User
) -> None:
    register = await client.post(
        "/couriers/me", json={"vehicle_type": "taxi", "zone": "Matam"}, headers=auth_headers(buyer_user)
    )
    courier_id = register.json()["id"]

    before = await client.get("/couriers")
    assert not any(c["id"] == courier_id for c in before.json())

    approve = await client.patch(
        f"/admin/couriers/{courier_id}", json={"status": "approved"}, headers=auth_headers(admin_user)
    )
    assert approve.status_code == 200

    after = await client.get("/couriers")
    matching = next(c for c in after.json() if c["id"] == courier_id)
    assert matching["vehicle_type"] == "taxi"
    assert matching["phone"] == buyer_user.phone


async def test_non_admin_cannot_validate_couriers(client: AsyncClient, buyer_user: User) -> None:
    response = await client.get("/admin/couriers", headers=auth_headers(buyer_user))

    assert response.status_code == 403


async def test_admin_can_create_courier_directly_and_approved(client: AsyncClient, admin_user: User) -> None:
    response = await client.post(
        "/admin/couriers",
        json={
            "phone": "+224655000099",
            "password": "partner-delivery-co",
            "first_name": "Fatoumata",
            "last_name": "Barry",
            "vehicle_type": "voiture",
            "zone": "Ratoma",
        },
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "approved"
    assert body["phone"] == "+224655000099"
    assert body["full_name"] == "Fatoumata Barry"

    login = await client.post("/auth/login", json={"phone": "+224655000099", "password": "partner-delivery-co"})
    assert login.status_code == 200


async def test_admin_create_courier_rejects_duplicate_phone(client: AsyncClient, admin_user: User, buyer_user: User) -> None:
    response = await client.post(
        "/admin/couriers",
        json={"phone": buyer_user.phone, "password": "whatever123", "vehicle_type": "moto"},
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 409


async def test_non_admin_cannot_create_courier(client: AsyncClient, buyer_user: User) -> None:
    response = await client.post(
        "/admin/couriers",
        json={"phone": "+224655000098", "password": "whatever123", "vehicle_type": "moto"},
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 403
