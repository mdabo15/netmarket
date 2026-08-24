"""Tests for the saved-addresses module: ownership, single default, GPS fields."""

from httpx import AsyncClient

from app.pickup_points.models import PickupPoint
from app.users.models import User
from tests.conftest import auth_headers, make_vendor


async def test_first_address_becomes_default_automatically(client: AsyncClient, buyer_user: User) -> None:
    response = await client.post(
        "/addresses",
        json={"label": "Maison", "zone": "Kaloum, près du marché"},
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 201
    assert response.json()["is_default"] is True


async def test_setting_a_new_default_unsets_the_previous_one(client: AsyncClient, buyer_user: User) -> None:
    headers = auth_headers(buyer_user)
    first = await client.post("/addresses", json={"label": "Maison", "zone": "Kaloum"}, headers=headers)
    await client.post(
        "/addresses", json={"label": "Bureau", "zone": "Matam", "is_default": True}, headers=headers
    )

    listing = await client.get("/addresses", headers=headers)
    defaults = [a for a in listing.json() if a["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["label"] == "Bureau"

    refreshed_first = next(a for a in listing.json() if a["id"] == first.json()["id"])
    assert refreshed_first["is_default"] is False


async def test_address_stores_gps_coordinates(client: AsyncClient, buyer_user: User) -> None:
    response = await client.post(
        "/addresses",
        json={"label": "Maison", "zone": "Kaloum", "latitude": 9.5370, "longitude": -13.6785},
        headers=auth_headers(buyer_user),
    )

    body = response.json()
    assert body["latitude"] == 9.5370
    assert body["longitude"] == -13.6785


async def test_gps_position_alone_is_enough_without_zone_text(client: AsyncClient, buyer_user: User) -> None:
    response = await client.post(
        "/addresses",
        json={"label": "Maison", "latitude": 9.5370, "longitude": -13.6785},
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 201
    assert response.json()["zone"] == ""


async def test_neither_zone_nor_gps_is_rejected(client: AsyncClient, buyer_user: User) -> None:
    response = await client.post("/addresses", json={"label": "Maison"}, headers=auth_headers(buyer_user))

    assert response.status_code == 422


async def test_update_cannot_clear_both_zone_and_position(client: AsyncClient, buyer_user: User) -> None:
    headers = auth_headers(buyer_user)
    created = await client.post(
        "/addresses", json={"label": "Maison", "latitude": 9.5370, "longitude": -13.6785}, headers=headers
    )

    response = await client.patch(f"/addresses/{created.json()['id']}", json={"latitude": None}, headers=headers)

    assert response.status_code == 409


async def test_pickup_point_address_type(client: AsyncClient, buyer_user: User, pickup_point: PickupPoint) -> None:
    response = await client.post(
        "/addresses",
        json={
            "label": "Point Wari Madina",
            "zone": "En face de la pharmacie",
            "delivery_type": "pickup_point",
            "pickup_point_id": str(pickup_point.id),
        },
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 201
    assert response.json()["delivery_type"] == "pickup_point"
    assert response.json()["pickup_point_id"] == str(pickup_point.id)


async def test_pickup_point_address_without_a_point_is_rejected(client: AsyncClient, buyer_user: User) -> None:
    # Régression : cette combinaison passait autrefois la validation (rien ne
    # vérifiait pickup_point_id), produisant une adresse enregistrée mais
    # inutilisable — le checkout la rejetait ensuite avec un 409 confus. Voir
    # AddressForm.vue::validateAddressForm côté frontend pour le même filet.
    response = await client.post(
        "/addresses",
        json={"label": "Point sans sélection", "zone": "En face de la pharmacie", "delivery_type": "pickup_point"},
        headers=auth_headers(buyer_user),
    )

    assert response.status_code == 422


async def test_update_to_pickup_point_without_a_point_is_rejected(client: AsyncClient, buyer_user: User) -> None:
    headers = auth_headers(buyer_user)
    created = await client.post("/addresses", json={"label": "Maison", "zone": "Kaloum"}, headers=headers)

    response = await client.patch(
        f"/addresses/{created.json()['id']}", json={"delivery_type": "pickup_point"}, headers=headers
    )

    assert response.status_code == 409


async def test_update_own_address(client: AsyncClient, buyer_user: User) -> None:
    headers = auth_headers(buyer_user)
    created = await client.post("/addresses", json={"label": "Maison", "zone": "Kaloum"}, headers=headers)

    response = await client.patch(
        f"/addresses/{created.json()['id']}", json={"zone": "Kaloum, nouveau repère"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["zone"] == "Kaloum, nouveau repère"


async def test_cannot_update_another_users_address(client: AsyncClient, db_session, buyer_user: User) -> None:
    headers = auth_headers(buyer_user)
    created = await client.post("/addresses", json={"label": "Maison", "zone": "Kaloum"}, headers=headers)

    other_user, _ = await make_vendor(db_session, phone="+224620009999", shop_name="Sans Rapport")
    response = await client.patch(
        f"/addresses/{created.json()['id']}", json={"zone": "Tentative"}, headers=auth_headers(other_user)
    )

    assert response.status_code == 404


async def test_delete_own_address(client: AsyncClient, buyer_user: User) -> None:
    headers = auth_headers(buyer_user)
    created = await client.post("/addresses", json={"label": "Maison", "zone": "Kaloum"}, headers=headers)

    response = await client.delete(f"/addresses/{created.json()['id']}", headers=headers)
    assert response.status_code == 200

    listing = await client.get("/addresses", headers=headers)
    assert listing.json() == []


async def test_addresses_require_authentication(client: AsyncClient) -> None:
    response = await client.get("/addresses")

    assert response.status_code == 401
