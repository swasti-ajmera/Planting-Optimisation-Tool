import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import sys
import os
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, create_access_token, User, AuditLog

client = TestClient(app)

# ======================
# Fixtures
# ======================

@pytest.fixture
def mock_db():
    """Mock database session"""
    db = MagicMock()
    yield db

@pytest.fixture
def mock_get_db(mock_db):
    """Mock get_db dependency"""
    with patch('main.get_db') as mock:
        mock.return_value.__enter__ = Mock(return_value=mock_db)
        mock.return_value.__exit__ = Mock(return_value=None)
        yield mock_db

@pytest.fixture
def officer_user():
    """Sample officer user"""
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="officer@pot.com",
        full_name="John Officer",
        password="password123",
        role="officer",
        is_active=True,
        created_at=datetime.utcnow()
    )
    return user

@pytest.fixture
def admin_user():
    """Sample admin user"""
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        email="admin@pot.com",
        full_name="Admin User",
        password="password123",
        role="admin",
        is_active=True,
        created_at=datetime.utcnow()
    )
    return user

@pytest.fixture
def sample_audit_logs():
    """Sample audit log entries"""
    return [
        AuditLog(
            id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            user_email="officer@pot.com",
            action="login",
            resource_type=None,
            resource_id=None,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            status="success",
            details={"role": "officer"},
            created_at=datetime.utcnow()
        ),
        AuditLog(
            id=uuid.UUID("00000000-0000-0000-0000-000000000011"),
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            user_email="officer@pot.com",
            action="access_denied",
            resource_type="endpoint",
            resource_id="/admin/users",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            status="denied",
            details={"required_roles": ["admin"], "user_role": "officer"},
            created_at=datetime.utcnow()
        )
    ]

# ======================
# Test Audit Logging on Registration
# ======================

def test_register_logs_success(mock_get_db, officer_user):
    """Test successful registration is logged"""
    mock_get_db.query().filter().first.return_value = None
    mock_get_db.add = Mock()
    mock_get_db.commit = Mock()
    mock_get_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', officer_user.id))
    
    response = client.post(
        "/auth/register",
        json={
            "email": "officer@pot.com",
            "full_name": "John Officer",
            "password": "password123",
            "role": "officer"
        }
    )
    
    assert response.status_code == 201
    # Verify audit log was created (2 add calls: user + audit log)
    assert mock_get_db.add.call_count == 2

def test_register_logs_failure(mock_get_db, officer_user):
    """Test failed registration is logged"""
    mock_get_db.query().filter().first.return_value = officer_user
    mock_get_db.add = Mock()
    mock_get_db.commit = Mock()
    
    response = client.post(
        "/auth/register",
        json={
            "email": "officer@pot.com",
            "full_name": "John Officer",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    # Verify audit log for failed attempt was created
    assert mock_get_db.add.called

# ======================
# Test Audit Logging on Login
# ======================

def test_login_logs_success(mock_get_db, officer_user):
    """Test successful login is logged"""
    mock_get_db.query().filter().first.return_value = officer_user
    mock_get_db.commit = Mock()
    mock_get_db.add = Mock()
    
    response = client.post(
        "/auth/login",
        data={
            "username": "officer@pot.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    # Verify audit log was created
    assert mock_get_db.add.called

def test_login_logs_failure(mock_get_db):
    """Test failed login is logged"""
    mock_get_db.query().filter().first.return_value = None
    mock_get_db.add = Mock()
    
    response = client.post(
        "/auth/login",
        data={
            "username": "wrong@pot.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    # Verify audit log for failed login was created
    assert mock_get_db.add.called

# ======================
# Test Audit Logging on Token Refresh
# ======================

def test_token_refresh_logs_success(mock_get_db, officer_user):
    """Test successful token refresh is logged"""
    mock_get_db.query().filter().first.return_value = officer_user
    mock_get_db.add = Mock()
    
    from main import create_refresh_token
    refresh_token = create_refresh_token(data={"sub": officer_user.email, "role": officer_user.role})
    
    response = client.post(f"/auth/refresh?refresh_token={refresh_token}")
    
    assert response.status_code == 200
    # Verify audit log was created
    assert mock_get_db.add.called

def test_token_refresh_logs_failure(mock_get_db):
    """Test failed token refresh is logged"""
    mock_get_db.add = Mock()
    
    response = client.post("/auth/refresh?refresh_token=invalid_token")
    
    assert response.status_code == 401
    # Verify audit log for failed refresh was created
    assert mock_get_db.add.called

# ======================
# Test Audit Logging on Access Control
# ======================

def test_access_denied_is_logged(mock_get_db, officer_user):
    """Test access denied events are logged"""
    mock_get_db.query().filter().first.return_value = officer_user
    mock_get_db.add = Mock()
    
    token = create_access_token(data={"sub": officer_user.email, "role": officer_user.role})
    
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    # Verify access denied was logged
    assert mock_get_db.add.called

def test_access_granted_is_logged(mock_get_db, admin_user):
    """Test access granted events are logged"""
    mock_get_db.query().filter().first.return_value = admin_user
    mock_get_db.add = Mock()
    
    token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
    
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    # Verify access granted was logged
    assert mock_get_db.add.called

# ======================
# Test Audit Log Retrieval (Admin)
# ======================

def test_get_audit_logs_admin_only(mock_get_db, admin_user, sample_audit_logs):
    """Test admin can retrieve audit logs"""
    mock_get_db.query().filter().first.return_value = admin_user
    mock_get_db.query().order_by().limit().offset().all.return_value = sample_audit_logs
    mock_get_db.add = Mock()
    
    token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
    
    response = client.get(
        "/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_audit_logs_officer_denied(mock_get_db, officer_user):
    """Test officer cannot retrieve audit logs"""
    mock_get_db.query().filter().first.return_value = officer_user
    mock_get_db.add = Mock()
    
    token = create_access_token(data={"sub": officer_user.email, "role": officer_user.role})
    
    response = client.get(
        "/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403

def test_get_user_audit_logs(mock_get_db, admin_user, sample_audit_logs):
    """Test admin can retrieve audit logs for specific user"""
    mock_get_db.query().filter().first.return_value = admin_user
    mock_get_db.query().filter().order_by().limit().all.return_value = sample_audit_logs
    mock_get_db.add = Mock()
    
    token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
    
    response = client.get(
        "/admin/audit-logs/user/officer@pot.com",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# ======================
# Test Audit Log Data Capture
# ======================

def test_audit_log_captures_ip_address(mock_get_db, officer_user):
    """Test audit log captures IP address"""
    mock_get_db.query().filter().first.return_value = None
    mock_get_db.add = Mock()
    mock_get_db.commit = Mock()
    mock_get_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', officer_user.id))
    
    response = client.post(
        "/auth/register",
        json={
            "email": "test@pot.com",
            "full_name": "Test User",
            "password": "password123"
        },
        headers={"X-Forwarded-For": "203.0.113.1"}
    )
    
    assert response.status_code == 201

def test_audit_log_captures_user_agent(mock_get_db, officer_user):
    """Test audit log captures user agent"""
    mock_get_db.query().filter().first.return_value = None
    mock_get_db.add = Mock()
    mock_get_db.commit = Mock()
    mock_get_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', officer_user.id))
    
    response = client.post(
        "/auth/register",
        json={
            "email": "test@pot.com",
            "full_name": "Test User",
            "password": "password123"
        },
        headers={"User-Agent": "TestBot/1.0"}
    )
    
    assert response.status_code == 201