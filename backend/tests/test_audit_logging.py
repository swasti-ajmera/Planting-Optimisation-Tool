import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.audit_log import AuditLog

pytestmark = pytest.mark.asyncio


async def test_audit_log_on_user_creation(
    async_client: AsyncClient, admin_auth_headers: dict, async_session: AsyncSession
):
    # Action that should trigger an audit log
    await async_client.post(
        "/users/",
        json={
            "email": "audituser@example.com",
            "name": "Audit User",
            "password": "auditpassword",
            "role": "officer",
        },
        headers=admin_auth_headers,
    )

    # Check that the audit log was created
    result = await async_session.execute(
        select(AuditLog).filter(AuditLog.event_type == "user_create")
    )
    log_entry = result.scalar_one_or_none()

    assert log_entry is not None
    assert "created user audituser@example.com" in log_entry.details
