import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import sys
import os
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, create_access_token, User

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
def supervisor_user():
    """Sample supervisor user"""
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        email="supervisor@pot.com",
        full_name="Jane Supervisor",
        password="password123",
        role="supervisor",
        is_active=True,
        created_at=datetime.utcnow()
    )
    return user

@pytest.fixture
def admin_user():
    """Sample admin user"""
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        email="admin@pot.com",
        full_name="Admin User",
        password="password123",
        role="admin",
        is_active=True,
        created_at=datetime.utcnow()
    )
    return user

# ======================
# Test User Registration with Roles
# ======================

def test_register_officer(mock_get_db, officer_user):
    """Test registering an officer"""
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
    assert response.json()["role"] == "officer"

def test_register_supervisor(mock_get_db, supervisor_user):
    """Test registering a supervisor"""
    mock_get_db.query().filter().first.return_value = None
    mock_get_db.add = Mock()
    mock_get_db.commit = Mock()
    mock_get_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', supervisor_user.id))
    
    response = client.post(
        "/auth/register",
        json={
            "email": "supervisor@pot.com",
            "full_name": "Jane Supervisor",
            "password": "password123",
            "role": "supervisor"
        }
    )
    assert response.status_code == 201
    assert response.json()["role"] == "supervisor"

def test_register_admin(mock_get_db, admin_user):
    """Test registering an admin"""
    mock_get_db.query().filter().first.return_value = None
    mock_get_db.add = Mock()
    mock_get_db.commit = Mock()
    mock_get_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', admin_user.id))
    
    response = client.post(
        "/auth/register",
        json={
            "email": "admin@pot.com",
            "full_name": "Admin User",
            "password": "password123",
            "role": "admin"
        }
    )
    assert response.status_code == 201
    assert response.json()["role"] == "admin"

def test_register_default_role(mock_get_db, officer_user):
    """Test default role is officer"""
    mock_get_db.query().filter().first.return_value = None
    mock_get_db.add = Mock()
    mock_get_db.commit = Mock()
    mock_get_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', officer_user.id))
    
    response = client.post(
        "/auth/register",
        json={
            "email": "officer@pot.com",
            "full_name": "John Officer",
            "password": "password123"
        }
    )
    assert response.status_code == 201

# ======================
# Test Login with Roles
# ======================

def test_login_includes_role(mock_get_db, officer_user):
    """Test login response includes role in token"""
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
    assert "access_token" in response.json()

# ======================
# Test Officer Access
# ======================

def test_officer_can_access_officer_dashboard(mock_get_db, officer_user):
    """Test officer can access officer dashboard"""
    mock_get_db.query().filter().first.return_value = officer_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": officer_user.email, "role": officer_user.role})
    
    response = client.get(
        "/officer/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "officer"

def test_officer_cannot_access_supervisor_reports(mock_get_db, officer_user):
    """Test officer cannot access supervisor reports"""
    mock_get_db.query().filter().first.return_value = officer_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": officer_user.email, "role": officer_user.role})
    
    response = client.get(
        "/supervisor/reports",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_officer_cannot_access_admin_panel(mock_get_db, officer_user):
    """Test officer cannot access admin panel"""
    mock_get_db.query().filter().first.return_value = officer_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": officer_user.email, "role": officer_user.role})
    
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

# ======================
# Test Supervisor Access
# ======================

def test_supervisor_can_access_officer_dashboard(mock_get_db, supervisor_user):
    """Test supervisor can access officer dashboard"""
    mock_get_db.query().filter().first.return_value = supervisor_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": supervisor_user.email, "role": supervisor_user.role})
    
    response = client.get(
        "/officer/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_supervisor_can_access_supervisor_reports(mock_get_db, supervisor_user):
    """Test supervisor can access supervisor reports"""
    mock_get_db.query().filter().first.return_value = supervisor_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": supervisor_user.email, "role": supervisor_user.role})
    
    response = client.get(
        "/supervisor/reports",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "supervisor"

def test_supervisor_cannot_access_admin_panel(mock_get_db, supervisor_user):
    """Test supervisor cannot access admin panel"""
    mock_get_db.query().filter().first.return_value = supervisor_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": supervisor_user.email, "role": supervisor_user.role})
    
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

# ======================
# Test Admin Access
# ======================

def test_admin_can_access_officer_dashboard(mock_get_db, admin_user):
    """Test admin can access officer dashboard"""
    mock_get_db.query().filter().first.return_value = admin_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
    
    response = client.get(
        "/officer/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_admin_can_access_supervisor_reports(mock_get_db, admin_user):
    """Test admin can access supervisor reports"""
    mock_get_db.query().filter().first.return_value = admin_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
    
    response = client.get(
        "/supervisor/reports",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_admin_can_access_admin_users(mock_get_db, admin_user):
    """Test admin can access admin user management"""
    mock_get_db.query().filter().first.return_value = admin_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
    
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"

def test_admin_can_access_admin_settings(mock_get_db, admin_user):
    """Test admin can access admin settings"""
    mock_get_db.query().filter().first.return_value = admin_user
    mock_get_db.add = Mock()
    token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
    
    response = client.get(
        "/admin/settings",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

# ======================
# Test Protected Route with Roles
# ======================

def test_protected_route_shows_role(mock_get_db, officer_user):
    """Test protected route returns user role"""
    mock_get_db.query().filter().first.return_value = officer_user
    token = create_access_token(data={"sub": officer_user.email, "role": officer_user.role})
    
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "officer"

# ======================
# Test Invalid Role Access
# ======================

def test_no_token_access_denied():
    """Test access denied without token"""
    response = client.get("/officer/dashboard")
    assert response.status_code == 401

def test_invalid_token_access_denied():
    """Test access denied with invalid token"""
    response = client.get(
        "/officer/dashboard",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401