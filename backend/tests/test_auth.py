import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import sys
import os
import uuid

# Add parent directory to path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import (
    app, 
    create_access_token, 
    create_refresh_token,
    get_user_by_email,
    create_user,
    authenticate_user,
    User
)

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
def sample_user():
    """Sample User SQLAlchemy object"""
    user = User(
        id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        email="test@example.com",
        full_name="Test User",
        password="password123",
        role="officer",
        is_active=True,
        created_at=datetime.utcnow()
    )
    return user

# ======================
# Test Utility Functions
# ======================

def test_create_access_token():
    """Test access token creation"""
    token = create_access_token(data={"sub": "test@example.com", "role": "officer"})
    assert token is not None
    assert len(token) > 0

def test_create_refresh_token():
    """Test refresh token creation"""
    token = create_refresh_token(data={"sub": "test@example.com", "role": "officer"})
    assert token is not None
    assert len(token) > 0

# ======================
# Test Database Functions
# ======================

def test_get_user_by_email(mock_db, sample_user):
    """Test getting user by email"""
    mock_db.query().filter().first.return_value = sample_user
    user = get_user_by_email(mock_db, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"

def test_get_user_by_email_not_found(mock_db):
    """Test getting non-existent user"""
    mock_db.query().filter().first.return_value = None
    user = get_user_by_email(mock_db, "nonexistent@example.com")
    assert user is None

def test_create_user(mock_db, sample_user):
    """Test creating a new user"""
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', sample_user.id))
    
    user = create_user(mock_db, "test@example.com", "Test User", "password123", "officer")
    assert user is not None
    assert user.email == "test@example.com"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

def test_authenticate_user_success(mock_db, sample_user):
    """Test user authentication with correct password"""
    mock_db.query().filter().first.return_value = sample_user
    user = authenticate_user(mock_db, "test@example.com", "password123")
    assert user is not False
    assert user.email == "test@example.com"

def test_authenticate_user_wrong_password(mock_db, sample_user):
    """Test authentication with wrong password"""
    mock_db.query().filter().first.return_value = sample_user
    user = authenticate_user(mock_db, "test@example.com", "wrongpassword")
    assert user is False

def test_authenticate_user_not_found(mock_db):
    """Test authentication with non-existent user"""
    mock_db.query().filter().first.return_value = None
    user = authenticate_user(mock_db, "nonexistent@example.com", "password123")
    assert user is False

# ======================
# Test API Endpoints
# ======================

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "POT Backend API - Planting Optimisation Tool"
    assert response.json()["status"] == "running"

def test_health_check(mock_get_db):
    """Test health check endpoint"""
    mock_get_db.execute = Mock()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_success(mock_get_db, sample_user):
    """Test user registration"""
    mock_get_db.query().filter().first.return_value = None
    mock_get_db.add = Mock()
    mock_get_db.commit = Mock()
    mock_get_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', sample_user.id))
    
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "password123",
            "role": "officer"
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert response.json()["full_name"] == "Test User"
    assert response.json()["role"] == "officer"

def test_register_duplicate_email(mock_get_db, sample_user):
    """Test registration with existing email"""
    mock_get_db.query().filter().first.return_value = sample_user
    mock_get_db.add = Mock()
    
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_success(mock_get_db, sample_user):
    """Test user login"""
    mock_get_db.query().filter().first.return_value = sample_user
    mock_get_db.commit = Mock()
    mock_get_db.add = Mock()
    
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_wrong_password(mock_get_db, sample_user):
    """Test login with wrong password"""
    mock_get_db.query().filter().first.return_value = sample_user
    mock_get_db.add = Mock()
    
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_login_user_not_found(mock_get_db):
    """Test login with non-existent user"""
    mock_get_db.query().filter().first.return_value = None
    mock_get_db.add = Mock()
    
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 401

def test_refresh_token_success(mock_get_db, sample_user):
    """Test token refresh"""
    mock_get_db.query().filter().first.return_value = sample_user
    mock_get_db.add = Mock()
    refresh_token = create_refresh_token(data={"sub": "test@example.com", "role": "officer"})
    
    response = client.post(f"/auth/refresh?refresh_token={refresh_token}")
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

def test_refresh_token_invalid(mock_get_db):
    """Test refresh with invalid token"""
    mock_get_db.add = Mock()
    response = client.post("/auth/refresh?refresh_token=invalid_token")
    assert response.status_code == 401

def test_get_current_user(mock_get_db, sample_user):
    """Test getting current user"""
    mock_get_db.query().filter().first.return_value = sample_user
    access_token = create_access_token(data={"sub": "test@example.com", "role": "officer"})
    
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["full_name"] == "Test User"
    assert response.json()["role"] == "officer"

def test_get_current_user_no_token():
    """Test getting current user without token"""
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_get_current_user_invalid_token():
    """Test getting current user with invalid token"""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_protected_route_success(mock_get_db, sample_user):
    """Test protected route with valid token"""
    mock_get_db.query().filter().first.return_value = sample_user
    access_token = create_access_token(data={"sub": "test@example.com", "role": "officer"})
    
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert "Hello Test User!" in response.json()["message"]
    assert response.json()["email"] == "test@example.com"
    assert response.json()["role"] == "officer"

def test_protected_route_no_token():
    """Test protected route without token"""
    response = client.get("/protected")
    assert response.status_code == 401