"""Tests for registration, login, refresh and role-protected routes."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User
from tests.conftest import auth_headers

REGISTER_PAYLOAD = {"phone": "+224621111111", "password": "password123"}


async def test_register_creates_buyer_account(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body

    me = await client.get("/users/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["role"] == "buyer"
    assert me.json()["phone"] == REGISTER_PAYLOAD["phone"]


async def test_register_rejects_duplicate_phone(client: AsyncClient) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 409
    assert response.json()["detail"] == "Ce numéro de téléphone est déjà utilisé."


async def test_register_rejects_invalid_phone_format(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={"phone": "0621111111", "password": "password123"})

    assert response.status_code == 422


async def test_login_success(client: AsyncClient) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)

    response = await client.post(
        "/auth/login", json={"phone": REGISTER_PAYLOAD["phone"], "password": REGISTER_PAYLOAD["password"]}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password_returns_generic_error(client: AsyncClient) -> None:
    await client.post("/auth/register", json=REGISTER_PAYLOAD)

    response = await client.post(
        "/auth/login", json={"phone": REGISTER_PAYLOAD["phone"], "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Numéro de téléphone ou mot de passe incorrect."


async def test_refresh_issues_new_token_pair(client: AsyncClient) -> None:
    register_response = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    refresh_token = register_response.json()["refresh_token"]

    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_refresh_rejects_access_token(client: AsyncClient) -> None:
    register_response = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    access_token = register_response.json()["access_token"]

    response = await client.post("/auth/refresh", json={"refresh_token": access_token})

    assert response.status_code == 401


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/users/me")

    assert response.status_code == 401


async def test_role_protected_route_rejects_wrong_role(
    client: AsyncClient, db_session: AsyncSession, buyer_user: User
) -> None:
    response = await client.post(
        "/categories", json={"name": "Mode"}, headers=auth_headers(buyer_user)
    )

    assert response.status_code == 403


async def test_role_protected_route_allows_admin(
    client: AsyncClient, db_session: AsyncSession, admin_user: User
) -> None:
    response = await client.post(
        "/categories", json={"name": "Mode"}, headers=auth_headers(admin_user)
    )

    assert response.status_code == 201
