import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import (
    app, 
    create_access_token, 
    create_refresh_token,
    get_user_by_email,
    create_user,
    authenticate_user
)

client = TestClient(app)

# ======================
# Fixtures
# ======================

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    with patch('main.supabase') as mock:
        yield mock

@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }

# ======================
# Test Utility Functions
# ======================

def test_create_access_token():
    """Test access token creation"""
    token = create_access_token(data={"sub": "test@example.com"})
    assert token is not None
    assert len(token) > 0

def test_create_refresh_token():
    """Test refresh token creation"""
    token = create_refresh_token(data={"sub": "test@example.com"})
    assert token is not None
    assert len(token) > 0

# ======================
# Test Database Functions
# ======================

def test_get_user_by_email(mock_supabase, sample_user):
    """Test getting user by email"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[sample_user])
    user = get_user_by_email("test@example.com")
    assert user is not None
    assert user["email"] == "test@example.com"

def test_get_user_by_email_not_found(mock_supabase):
    """Test getting non-existent user"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[])
    user = get_user_by_email("nonexistent@example.com")
    assert user is None

def test_create_user(mock_supabase, sample_user):
    """Test creating a new user"""
    mock_supabase.table().insert().execute.return_value = Mock(data=[sample_user])
    user = create_user("test@example.com", "Test User", "password123")
    assert user is not None
    assert user["email"] == "test@example.com"

def test_authenticate_user_success(mock_supabase, sample_user):
    """Test user authentication with correct password"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[sample_user])
    user = authenticate_user("test@example.com", "password123")
    assert user is not False
    assert user["email"] == "test@example.com"

def test_authenticate_user_wrong_password(mock_supabase, sample_user):
    """Test authentication with wrong password"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[sample_user])
    user = authenticate_user("test@example.com", "wrongpassword")
    assert user is False

def test_authenticate_user_not_found(mock_supabase):
    """Test authentication with non-existent user"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[])
    user = authenticate_user("nonexistent@example.com", "password123")
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

def test_health_check(mock_supabase):
    """Test health check endpoint"""
    mock_supabase.table().select().limit().execute.return_value = Mock()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_success(mock_supabase, sample_user):
    """Test user registration"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[])
    mock_supabase.table().insert().execute.return_value = Mock(data=[sample_user])
    
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert response.json()["full_name"] == "Test User"

def test_register_duplicate_email(mock_supabase, sample_user):
    """Test registration with existing email"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[sample_user])
    
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

def test_login_success(mock_supabase, sample_user):
    """Test user login"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[sample_user])
    mock_supabase.table().update().eq().execute.return_value = Mock()
    
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

def test_login_wrong_password(mock_supabase, sample_user):
    """Test login with wrong password"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[sample_user])
    
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_login_user_not_found(mock_supabase):
    """Test login with non-existent user"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[])
    
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 401

def test_refresh_token_success(mock_supabase, sample_user):
    """Test token refresh"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[sample_user])
    refresh_token = create_refresh_token(data={"sub": "test@example.com"})
    
    response = client.post(f"/auth/refresh?refresh_token={refresh_token}")
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

def test_refresh_token_invalid(mock_supabase):
    """Test refresh with invalid token"""
    response = client.post("/auth/refresh?refresh_token=invalid_token")
    assert response.status_code == 401

def test_get_current_user(mock_supabase, sample_user):
    """Test getting current user"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[sample_user])
    access_token = create_access_token(data={"sub": "test@example.com"})
    
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["full_name"] == "Test User"

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

def test_protected_route_success(mock_supabase, sample_user):
    """Test protected route with valid token"""
    mock_supabase.table().select().eq().execute.return_value = Mock(data=[sample_user])
    access_token = create_access_token(data={"sub": "test@example.com"})
    
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert "Hello Test User!" in response.json()["message"]
    assert response.json()["email"] == "test@example.com"

def test_protected_route_no_token():
    """Test protected route without token"""
    response = client.get("/protected")
    assert response.status_code == 401