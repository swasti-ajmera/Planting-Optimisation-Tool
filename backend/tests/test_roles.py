import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# Test user creation endpoint
async def test_create_user_by_admin(
    async_client: AsyncClient, admin_auth_headers: dict
):
    response = await async_client.post(
        "/users/",
        json={
            "email": "testuser@example.com",
            "name": "Test User",
            "password": "testpassword",
            "role": "officer",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201


async def test_create_user_by_supervisor_fail(
    async_client: AsyncClient, supervisor_auth_headers: dict
):
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
    assert response.status_code == 403


# Test reading user information
async def test_read_users_by_supervisor(
    async_client: AsyncClient, supervisor_auth_headers: dict
):
    response = await async_client.get("/users/", headers=supervisor_auth_headers)
    assert response.status_code == 200


async def test_read_users_by_admin(
    async_client: AsyncClient, admin_auth_headers: dict
):
    response = await async_client.get("/users/", headers=admin_auth_headers)
    assert response.status_code == 200


async def test_read_users_by_officer_fail(
    async_client: AsyncClient, officer_auth_headers: dict
):
    response = await async_client.get("/users/", headers=officer_auth_headers)
    assert response.status_code == 403


# Test role hierarchy
async def test_admin_can_access_supervisor_endpoint(
    async_client: AsyncClient, admin_auth_headers: dict
):
    response = await async_client.get("/users/", headers=admin_auth_headers)
    assert response.status_code == 200
