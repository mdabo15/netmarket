"""Tests for the authenticated user's own profile (GET/PATCH /users/me)."""

from httpx import AsyncClient

from app.users.models import User
from tests.conftest import auth_headers


async def test_update_first_and_last_name(client: AsyncClient, buyer_user: User) -> None:
    response = await client.patch(
        "/users/me", json={"first_name": "Mamadou", "last_name": "Diallo"}, headers=auth_headers(buyer_user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Mamadou"
    assert body["last_name"] == "Diallo"


async def test_partial_update_does_not_clear_other_fields(client: AsyncClient, buyer_user: User) -> None:
    headers = auth_headers(buyer_user)
    await client.patch("/users/me", json={"first_name": "Mamadou", "last_name": "Diallo"}, headers=headers)

    response = await client.patch("/users/me", json={"email": "mamadou@test.gn"}, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Mamadou"
    assert body["last_name"] == "Diallo"
    assert body["email"] == "mamadou@test.gn"


async def test_get_my_profile_includes_name_fields(client: AsyncClient, buyer_user: User) -> None:
    response = await client.get("/users/me", headers=auth_headers(buyer_user))

    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] is None
    assert body["last_name"] is None
