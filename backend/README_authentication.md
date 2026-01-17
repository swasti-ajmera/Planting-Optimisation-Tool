# POT Backend - Authentication & Authorization System

Complete authentication and authorization system with JWT tokens, role-based access control, and comprehensive audit logging.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [User Roles](#user-roles)
- [Audit Logging](#audit-logging)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- ✅ **JWT Authentication** - Secure token-based authentication with access and refresh tokens
- ✅ **Role-Based Access Control (RBAC)** - Three user roles: Officer, Supervisor, Admin
- ✅ **Audit Logging** - Comprehensive logging of all user actions and system events
- ✅ **PostgreSQL Database** - Reliable relational database with SQLAlchemy ORM
- ✅ **FastAPI Framework** - Modern, fast web framework with automatic API documentation
- ✅ **Comprehensive Testing** - 59 unit tests with 100% coverage of authentication logic

---

## 🛠 Tech Stack

- **Backend Framework**: FastAPI 0.122.0+
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **Authentication**: JWT (python-jose)
- **Testing**: Pytest 9.0+
- **Package Manager**: uv
- **Containerization**: Docker & Docker Compose

---

## 📁 Project Structure

```
backend/
├── main.py                    # Main application file
├── pyproject.toml            # Python dependencies
├── .env                      # Environment variables (create this)
├── docker-compose.yml        # PostgreSQL container setup
├── Justfile                  # Command shortcuts
├── tests/                    # Test directory
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration
│   ├── test_auth.py         # Authentication tests (22 tests)
│   ├── test_roles.py        # Role-based access tests (21 tests)
│   └── test_audit_logs.py   # Audit logging tests (16 tests)
└── README_Authentication.md  # This file
```

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.12+**
   ```bash
   python --version
   ```

2. **uv** (Python package manager)
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or on Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Docker** (for PostgreSQL)
   - Download from: https://www.docker.com/get-started

4. **Just** (command runner - optional but recommended)
   ```bash
   # Windows
   winget install --id Casey.Just --exact
   
   # Linux
   sudo apt install just
   
   # macOS
   brew install just
   ```

---

## 🚀 Installation

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Install Python Dependencies

```bash
uv sync
```

This will install all required packages from `pyproject.toml`:
- FastAPI
- SQLAlchemy
- PostgreSQL driver (psycopg2)
- JWT libraries (python-jose)
- Testing tools (pytest, pytest-cov)
- And more...

---

## 🗄 Database Setup

### Option 1: Using Docker Compose (Recommended)

#### 1. Create `docker-compose.yml`

If not already present, create this file in the `backend/` directory:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: pot_postgres_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: POT_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

#### 2. Start PostgreSQL

Using `just`:
```bash
just db-start
```

Or using Docker directly:
```bash
docker compose up -d db
```

#### 3. Verify Database is Running

```bash
docker ps | grep pot_postgres_db
```

### Option 2: Local PostgreSQL Installation

If you prefer installing PostgreSQL directly:

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb POT_db
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
createdb POT_db
```

**Windows:**
- Download installer from: https://www.postgresql.org/download/windows/
- Install with default settings
- Create database using pgAdmin or command line

---

## ⚙️ Configuration

### Create `.env` File

Create a `.env` file in the `backend/` directory:

```bash
# Copy the example
cp .env.example .env

# Or create manually
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/POT_db

# JWT Secret Key (use a strong random key in production)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Optional: Token expiry settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF
```

### Generate a Secure Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and replace `your-super-secret-key-change-this-in-production` in your `.env` file.

### Database Tables

Tables are **automatically created** when you first run the application thanks to:
```python
Base.metadata.create_all(bind=engine)
```

The following tables will be created:
- `users` - User accounts with roles
- `audit_logs` - Audit trail of all actions

---

## 🏃 Running the Application

### Method 1: Using Just (Recommended)

```bash
# Start the application
just run

# Or if Justfile doesn't exist, create it:
just --init
```

### Method 2: Using uv Directly

```bash
uv run uvicorn main:app --reload
```

### Method 3: Using Python Directly

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the application
uvicorn main:app --reload
```

### Expected Output

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Access the Application

- **API Base URL**: http://localhost:8000
- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🧪 Testing

### Run All Tests

```bash
# Using just
just test

# Using uv
uv run pytest

# Using pytest directly
pytest
```

### Run Specific Test File

```bash
# Authentication tests (22 tests)
uv run pytest tests/test_auth.py -v

# Role-based access tests (21 tests)
uv run pytest tests/test_roles.py -v

# Audit logging tests (16 tests)
uv run pytest tests/test_audit_logs.py -v
```

### Run Tests with Coverage

```bash
# Generate coverage report
uv run pytest --cov=main --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=main --cov-report=html

# View HTML report (creates htmlcov/index.html)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Specific Test Function

```bash
uv run pytest tests/test_auth.py::test_login_success -v
```

### Run Tests with Different Verbosity

```bash
# Minimal output
pytest -q

# Verbose output
pytest -v

# Very verbose output
pytest -vv
```

### Expected Test Results

```
============================== test session starts ===============================
collected 59 items

tests/test_auth.py::test_create_access_token PASSED                        [  1%]
tests/test_auth.py::test_create_refresh_token PASSED                       [  3%]
...
tests/test_roles.py::test_admin_can_access_admin_settings PASSED           [ 89%]
tests/test_audit_logs.py::test_audit_log_captures_user_agent PASSED        [100%]

============================== 59 passed in 2.45s ================================
```

---

## 📚 API Documentation

### Authentication Endpoints

#### 1. Register New User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "securepassword",
  "role": "officer"  // optional, defaults to "officer"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "officer",
  "created_at": "2024-12-14T10:30:00Z"
}
```

#### 2. Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Refresh Token
```http
POST /auth/refresh?refresh_token=YOUR_REFRESH_TOKEN
```

#### 4. Get Current User
```http
GET /auth/me
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Protected Endpoints

#### Officer Dashboard (All Authenticated Users)
```http
GET /officer/dashboard
Authorization: Bearer YOUR_ACCESS_TOKEN
```

#### Supervisor Reports (Supervisor & Admin)
```http
GET /supervisor/reports
Authorization: Bearer YOUR_ACCESS_TOKEN
```

#### Admin Endpoints (Admin Only)
```http
GET /admin/users
GET /admin/settings
GET /admin/audit-logs?limit=100&offset=0
GET /admin/audit-logs/user/{email}
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Example Usage with cURL

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@pot.com",
    "full_name": "Admin User",
    "password": "admin123",
    "role": "admin"
  }'

# 2. Login and save token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -d "username=admin@pot.com&password=admin123" | jq -r '.access_token')

# 3. Access protected endpoint
curl http://localhost:8000/admin/users \
  -H "Authorization: Bearer $TOKEN"

# 4. Get audit logs
curl http://localhost:8000/admin/audit-logs \
  -H "Authorization: Bearer $TOKEN"
```

---

## 👥 User Roles

### Role Hierarchy

| Role | Level | Description |
|------|-------|-------------|
| **Officer** | 1 | Basic field officers - can view own data |
| **Supervisor** | 2 | Team supervisors - can view team data and reports |
| **Admin** | 3 | System administrators - full access to all features |

### Access Control Matrix

| Endpoint | Officer | Supervisor | Admin |
|----------|---------|------------|-------|
| `/officer/dashboard` | ✅ | ✅ | ✅ |
| `/supervisor/reports` | ❌ | ✅ | ✅ |
| `/admin/users` | ❌ | ❌ | ✅ |
| `/admin/settings` | ❌ | ❌ | ✅ |
| `/admin/audit-logs` | ❌ | ❌ | ✅ |

### Creating Users with Different Roles

```python
# Officer (default)
{
  "email": "officer@pot.com",
  "full_name": "John Officer",
  "password": "password123"
}

# Supervisor
{
  "email": "supervisor@pot.com",
  "full_name": "Jane Supervisor",
  "password": "password123",
  "role": "supervisor"
}

# Admin
{
  "email": "admin@pot.com",
  "full_name": "Admin User",
  "password": "password123",
  "role": "admin"
}
```

---

## 📊 Audit Logging

### What Gets Logged

Every important action is automatically logged:

- ✅ **User Registration** (success/failure)
- ✅ **Login Attempts** (success/failure)
- ✅ **Token Refresh** (success/failure)
- ✅ **Access Granted** (when user accesses protected routes)
- ✅ **Access Denied** (when user lacks permissions)
- ✅ **User Management** (create/update/delete operations)

### Audit Log Structure

```json
{
  "id": "uuid",
  "user_id": "user-uuid",
  "user_email": "user@example.com",
  "action": "login",
  "resource_type": "endpoint",
  "resource_id": "/admin/users",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "status": "success",
  "details": {
    "role": "admin"
  },
  "created_at": "2024-12-14T10:30:00Z"
}
```

### Viewing Audit Logs

```bash
# Get recent audit logs (Admin only)
curl http://localhost:8000/admin/audit-logs?limit=50 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get logs for specific user
curl http://localhost:8000/admin/audit-logs/user/officer@pot.com \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Audit Log Actions

- `login` - User login attempt
- `logout` - User logout
- `register` - User registration
- `token_refresh` - Token refresh
- `access_granted` - Successful access to protected resource
- `access_denied` - Failed access attempt
- `user_created` - New user created
- `user_updated` - User information updated
- `user_deleted` - User deleted

---

## 🛠 Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error:** `Could not connect to database`

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep pot_postgres_db

# If not running, start it
just db-start

# Check database logs
docker logs pot_postgres_db
```

#### 2. Port 5432 Already in Use

**Error:** `port 5432 is already allocated`

**Solution:**
```bash
# Find what's using port 5432
lsof -i :5432  # macOS/Linux
netstat -ano | findstr :5432  # Windows

# Stop existing PostgreSQL
docker compose down

# Or stop system PostgreSQL
sudo systemctl stop postgresql  # Linux
brew services stop postgresql@15  # macOS
```

#### 3. Tables Not Created

**Error:** `relation "users" does not exist`

**Solution:**
Tables are auto-created on first run. If they're missing:

```bash
# Connect to database
just psql

# Create tables manually
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
    role VARCHAR NOT NULL DEFAULT 'officer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    user_email VARCHAR,
    action VARCHAR NOT NULL,
    resource_type VARCHAR,
    resource_id VARCHAR,
    ip_address VARCHAR,
    user_agent TEXT,
    status VARCHAR NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. ModuleNotFoundError

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Make sure dependencies are installed
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows
```

#### 5. SECRET_KEY Not Set

**Error:** `SECRET_KEY must be set`

**Solution:**
```bash
# Create .env file
echo 'SECRET_KEY=your-secret-key' > .env

# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 6. Tests Failing

**Error:** Various test failures

**Solution:**
```bash
# Make sure database is NOT running during tests
# Tests use mocks, not real database
docker compose stop

# Run tests
uv run pytest

# If still failing, check imports
cd backend
uv run pytest -v
```

---

## 🔒 Security Best Practices

### In Production

1. **Use Strong SECRET_KEY**
   ```bash
   # Generate secure key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Enable HTTPS**
   - Never send tokens over HTTP
   - Use SSL/TLS certificates

3. **Update CORS Settings**
   ```python
   # In main.py, replace:
   allow_origins=["*"]
   
   # With:
   allow_origins=["https://yourdomain.com"]
   ```

4. **Use Environment Variables**
   - Never commit `.env` file
   - Use secrets management in production

5. **Implement Rate Limiting**
   - Prevent brute force attacks
   - Limit login attempts

6. **Enable Password Hashing**
   - Current implementation uses plain text (for demo)
   - In production, use bcrypt or argon2

7. **Set Token Expiry**
   - Short access tokens (15-30 min)
   - Longer refresh tokens (7 days)

---

## 📖 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org
- **JWT Introduction**: https://jwt.io/introduction
- **PostgreSQL Documentation**: https://www.postgresql.org/docs

---

## 🤝 Contributing

When contributing to authentication features:

1. Write tests first (TDD approach)
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov=main`
4. Follow existing code style
5. Update documentation

---

## 📝 Summary

You now have a complete authentication system with:

- ✅ JWT-based authentication
- ✅ Three user roles with access control
- ✅ Comprehensive audit logging
- ✅ 59 passing tests
- ✅ Full API documentation
- ✅ Production-ready PostgreSQL setup

**Next Steps:**
1. Start the database: `just db-start`
2. Run the application: `just run`
3. Open Swagger UI: http://localhost:8000/docs
4. Create your first admin user
5. Start building your application features!

---

**Questions or Issues?** Check the [Troubleshooting](#troubleshooting) section or review the test files for usage examples.