import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.user import User

pytestmark = pytest.mark.asyncio


async def test_register_user(async_client: AsyncClient, async_session: AsyncSession):
    response = await async_client.post(
        "/auth/register",
        json={
            "email": "newuser@test.com",
            "name": "New User",
            "password": "newpassword",
            "role": "officer",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert "id" in data
    assert "password" not in data

    result = await async_session.execute(
        select(User).filter(User.email == "newuser@test.com")
    )
    db_user = result.scalar_one_or_none()
    assert db_user is not None


async def test_login_for_access_token(
    async_client: AsyncClient, test_admin_user: User
):
    response = await async_client.post(
        "/auth/token",
        data={"username": "admin@test.com", "password": "adminpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(async_client: AsyncClient, test_admin_user: User):
    response = await async_client.post(
        "/auth/token",
        data={"username": "admin@test.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_login_wrong_username(async_client: AsyncClient, test_admin_user: User):
    response = await async_client.post(
        "/auth/token",
        data={"username": "wronguser@test.com", "password": "adminpassword"},
    )
    assert response.status_code == 401


async def test_get_current_user(async_client: AsyncClient, admin_auth_headers: dict):
    response = await async_client.get("/auth/users/me", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
