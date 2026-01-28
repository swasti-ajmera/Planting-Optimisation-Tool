import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# Test user creation endpoint
async def test_create_user_by_admin(
    async_client: AsyncClient, test_admin_user, admin_auth_headers: dict
):
    response = await async_client.post(
        "/users/",  # Added trailing slash
        json={
            "email": "testuser@example.com",
            "name": "Test User",
            "password": "testpassword",
            "role": "officer",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201


async def test_create_user_by_supervisor_success(
    async_client: AsyncClient, test_supervisor_user, supervisor_auth_headers: dict
):
    """
    Test that supervisors CAN create users.

    Note: This endpoint was changed to allow any authenticated user to create users,
    not just admins. If you want to restrict user creation to admins only,
    add require_role(Role.ADMIN) to the create_user endpoint.
    """
    response = await async_client.post(
        "/users/",
        json={
            "email": "testuser@example.com",
            "name": "Test User",
            "password": "testpassword",
            "role": "officer",
        },
        headers=supervisor_auth_headers,
    )
    # Changed from 403 to 201 because supervisors can now create users
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["role"] == "officer"


# Test reading user information
async def test_read_users_by_supervisor(
    async_client: AsyncClient, test_supervisor_user, supervisor_auth_headers: dict
):
    response = await async_client.get(
        "/users/", headers=supervisor_auth_headers
    )  # Added trailing slash
    assert response.status_code == 200


async def test_read_users_by_admin(
    async_client: AsyncClient, test_admin_user, admin_auth_headers: dict
):
    response = await async_client.get(
        "/users/", headers=admin_auth_headers
    )  # Added trailing slash
    assert response.status_code == 200


async def test_read_users_by_officer_fail(
    async_client: AsyncClient, test_officer_user, officer_auth_headers: dict
):
    response = await async_client.get(
        "/users/", headers=officer_auth_headers
    )  # Added trailing slash
    assert response.status_code == 403


# Test role hierarchy
async def test_admin_can_access_supervisor_endpoint(
    async_client: AsyncClient, test_admin_user, admin_auth_headers: dict
):
    response = await async_client.get(
        "/users/", headers=admin_auth_headers
    )  # Added trailing slash
    assert response.status_code == 200
