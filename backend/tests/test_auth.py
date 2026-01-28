import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.user import User

pytestmark = pytest.mark.asyncio


async def test_register_user(async_client: AsyncClient, async_session: AsyncSession):
    """
    Test user registration via /auth/register endpoint.

    Verifies that:
    - A new user can be created through the registration endpoint
    - The response includes user data without the password
    - The user is persisted in the database
    """
    response = await async_client.post(
        "/auth/register",
        json={
            "email": "newuser@test.com",
            "name": "Registration Test User",  # Changed to avoid name conflicts
            "password": "newpassword",
            "role": "officer",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["name"] == "Registration Test User"
    assert "id" in data
    assert "password" not in data  # Password should never be returned
    assert data["role"] == "officer"

    # Verify the user was actually created in the database
    result = await async_session.execute(
        select(User).filter(User.email == "newuser@test.com")
    )
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.name == "Registration Test User"


async def test_login_for_access_token(async_client: AsyncClient, test_admin_user: User):
    """
    Test successful login via /auth/token endpoint.

    Verifies that:
    - Valid credentials return a JWT access token
    - Token type is "bearer"
    - Response follows OAuth2 token format
    """
    response = await async_client.post(
        "/auth/token",
        data={"username": "admin@test.com", "password": "adminpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(async_client: AsyncClient, test_admin_user: User):
    """
    Test login failure with incorrect password.

    Verifies that authentication fails (401 Unauthorized) when
    the email is correct but the password is wrong.
    """
    response = await async_client.post(
        "/auth/token",
        data={"username": "admin@test.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_login_wrong_username(async_client: AsyncClient, test_admin_user: User):
    """
    Test login failure with non-existent user.

    Verifies that authentication fails (401 Unauthorized) when
    attempting to login with an email that doesn't exist.
    """
    response = await async_client.post(
        "/auth/token",
        data={"username": "wronguser@test.com", "password": "adminpassword"},
    )
    assert response.status_code == 401


async def test_get_current_user(async_client: AsyncClient, admin_auth_headers: dict):
    """
    Test retrieving current user information via /auth/users/me.

    Verifies that:
    - An authenticated user can retrieve their own information
    - The correct user data is returned based on the JWT token
    - Password is not included in the response
    """
    response = await async_client.get("/auth/users/me", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert "password" not in data  # Password should never be returned
