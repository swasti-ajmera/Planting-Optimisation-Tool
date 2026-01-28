# Backend README

## Folder structure:

```
backend/
├── alembic/                # Database migration scripts and history
│   └── versions/           # Migration files
├── init-db/                # Initial SQL scripts for container setup
├── src/                    # Main application source code
│   ├── domains/            # Domain data contracts for integration of features
│   ├── keys/               # Service account credentials
│   ├── models/             # SQLAlchemy database models
│   ├── routers/            # FastAPI route definitions (API endpoints)
│   ├── schemas/            # Pydantic models for data validation
│   ├── scripts/            # Scripts for initial database ingestion
│   │   └── data/           # Seeding data for scripts
│   └── services/           # Service layer connectivity
└── tests/                  # Pytest suite for automated testing
├── ERD.md                  # Entity-Relationship Diagram of current database
├── README.md               # This file
├── SCHEMA.md               # Current database schema
├── alembic.ini             # Alembic configuration file
├── docker-compose.yaml     # Configuration file for the database container
├── justfile                # Command runner for common project tasks/shortcuts
├── pyproject.toml          # Project metadata and dependencies list
└── uv.lock                 # Lockfile for python dependencies

```


## Infrastructure

#### Database
The database is a containerized PostGIS image - defined in docker-compose.yaml
Some of the PostGIS extensions bundled with the image are removed by init-db/01-remove-extensions.sql

The database migrations are handled by alembic and frequently used commands are defined in the justfile.
Revisions are stored in alembic/versions and are timestamped with a revision message, defined in alembic.ini

#### API

The API is built with FastAPI and provides RESTful endpoints for the application.

#### Authentication & Authorization

The application uses JWT (JSON Web Token) based authentication with role-based access control (RBAC).

**Authentication Flow:**

1. User logs in with email and password via `/token` endpoint
2. Password is verified against bcrypt hash in database
3. JWT access token is returned for subsequent requests
4. Token is sent in `Authorization: Bearer <token>` header

**User Roles (Hierarchical):**

- `officer` (level 1): Basic user permissions
- `supervisor` (level 2): Can view/manage users and resources
- `admin` (level 3): Full system access

Higher roles inherit all permissions of lower roles.

**Security Features:**

- Passwords hashed with bcrypt (never stored in plain text)
- JWT tokens for stateless authentication
- Role-based permission checks via `require_role()` dependency
- Audit logging for security events (login, user modifications, etc.)

**User Registration:**

To register a new user, send a POST request to `/auth/register`:

```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword123",
  "role": "officer"
}
```

- `email`: Valid email address (required, must be unique)
- `name`: User's full name (required)
- `password`: Password with minimum 8 characters (required)
- `role`: One of `officer`, `supervisor`, or `admin` (optional, defaults to `officer`)

Response returns the created user (without password):

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "officer"
}
```

**Login:**

To obtain an access token, send a POST request to `/auth/token` with form data:

```text
username=user@example.com&password=securepassword123
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Use the token in subsequent requests: `Authorization: Bearer <access_token>`

**Role-Based Permission Checks:**

The following endpoints have role-based access control implemented:

| Endpoint | Method | Required Role | Description |
| :--- | :--- | :--- | :--- |
| `/users/` | GET | SUPERVISOR | List all users |
| `/users/{user_id}` | GET | SUPERVISOR | Get user by ID |
| `/users/{user_id}` | PUT | ADMIN | Update user information |
| `/users/{user_id}` | DELETE | ADMIN | Delete user account |
| `/farms/` | POST | SUPERVISOR | Create new farm |
| `/farms/{farm_id}` | GET | OFFICER | Read farm by ID |
| `/species/` | POST | SUPERVISOR | Create new species |
| `/environmental-profile/` | POST | OFFICER | Get environmental profile |
| `/sapling-estimation/` | POST | OFFICER | Calculate sapling estimation |
| `/recommendations/` | POST | OFFICER | Generate recommendations |
| `/recommendations/{farm_id}` | GET | OFFICER | Get farm recommendations |

Notes:

- Due to hierarchical permissions, higher roles can access lower-level endpoints
- ADMIN can access SUPERVISOR and OFFICER endpoints
- SUPERVISOR can access OFFICER endpoints
- Protected endpoints return `403 Forbidden` if the user lacks required permissions

**Key Files:**

- [src/services/authentication.py](src/services/authentication.py): Password hashing, JWT validation, role checking
- [src/models/user.py](src/models/user.py:1): User model with role field
- [src/models/audit_log.py](src/models/audit_log.py:1): Audit log model for security events
- [src/routers/auth.py](src/routers/auth.py:1): Login and authentication endpoints




# Project Command References
## 1. Virtual Environment & Dependencies

These commands establish the isolated Python environment and install all necessary packages.
| Command |	Purpose | Step |
|---|---|---|
|`uv venv`|	Creates the isolated Python virtual environment (.venv). (Only done once). | Setup |
|`uv sync`|	Reads pyproject.toml and installs all dependencies into the .venv. | Setup/Updates |
|`source .venv/bin/activate`|	Activates the virtual environment, making the installed package executables (alembic, pytest) available in the terminal. | Pre-Execution |
|`deactivate`|	Exits the virtual environment and returns to the system shell. | Cleanup | 

## 2. Database Container Management

These commands use Docker to manage the PostgreSQL database instance.
| Command |	Purpose | Step |
|---|---|---|
|`docker compose up -d`| Creates (if necessary) and starts the PostgreSQL service (pot_postgres_db) in the background (-d). | Pre-Execution |
|`docker compose down` | Stops and removes the database container and its network. (Use this for a clean shutdown). | Cleanup |
| `docker exec -it pot_postgres_db psql -U postgres -d POT_db` | Opens an interactive command-line shell (psql) inside the running container for direct database inspection. | Debugging/Inspection |

## 3. Alembic Migrations & Schema

These commands manage the evolution of the database schema.
| Command |	Purpose | Step |
|---|---|---|
| `uv run dotenv run alembic revision --autogenerate -m "..."` | Detects changes in SQLAlchemy models and generates a new migration script file in the alembic/versions/ directory. | Schema Development |
| `alembic upgrade head` | Applies all outstanding migration scripts up to the most recent one (head), creating or altering tables in the database. | Core Execution |
| ` alembic stamp <revision_id>` | Forces the database's alembic_version table to record a specific revision ID without running any SQL. (Used to fix broken history). | Debugging/Recovery |

## 4. Development & Debugging Utilities

These commands are used to check, verify, and document the backend components.
| Command | Purpose | Step |
|---|---|---|
| `uv run dotenv run pytest` | Executes the test suite, ensuring code quality and infrastructure stability (requires configuration). | Testing |
| `python backend/src/print_schema.py > SCHEMA.md` | Executes print_schema.py script to output the current SQLAlchemy schema definition into a formatted Markdown file. | Documentation |

These commands establish the isolated Python environment and install all necessary packages.
| Command |	Purpose | Step |
|---|---|---|
|`uv venv`|	Creates the isolated Python virtual environment (.venv). (Only done once). | Setup |
|`uv sync`|	Reads pyproject.toml and installs all dependencies into the .venv. | Setup/Updates |
|`source .venv/bin/activate`|	Activates the virtual environment, making the installed package executables (alembic, pytest) available in the terminal. | Pre-Execution |
|`deactivate`|	Exits the virtual environment and returns to the system shell. | Cleanup | 


## Install [just](https://github.com/casey/just) using:


Windows:
```bash
winget install --id Casey.Just --exact
```
Linux/MacOS:
```bash
apt install just
```

## Justfile commands

run `just [target]` in `/backend` to execute.

| Target | Purpose | Shell Commands Executed |
| :--- | :--- | :--- |
| **`help`** | Shows all available `just` commands | Iterates over all targets and outputs to the terminal |
| **`stop`** | Stops the PostgreSQL container. | `docker compose down` |
| **`start`** | Ensures a clean state (`stop`) then starts the PostgreSQL container service in detached mode. | 1. `docker compose down -v` (via `stop`) 2. `docker compose up -d db` 3. `sleep 5` |
| **`setup`** | Initializes the database container from scratch (`stop`, `start`, `migrate`, ), starts the service, and applies all pending Alembic migrations. | 1. `docker compose down` (via `stop`)<br> 2. `docker compose up -d db` (via `start`)<br> 3. `sleep 5` <br> 4. **`uv run dotenv run alembic upgrade head` (via `migrate`)** |
| **`revision`** | **GENERATES** a new Alembic migration script based on changes detected in your Python models. **Requires `M="message"`**. After running, you must **review the script** before running `just migrate`. | `uv run dotenv run alembic revision --autogenerate -m "message"` |
| **`migrate`** | Applies any pending Alembic migration scripts to upgrade the database schema to the latest version. This is the final step after creating and reviewing a script. | `uv run dotenv run alembic upgrade head` |
| **`populate`** | Wipes the DB, migrates, and ingests all CSV data. Outputs state of database setup statistics to terminal | Runs `setup_import_db.py` |
| **`test`** | Executes the full test suite using Pytest on the contents of the `tests/` directory. | `uv run dotenv run pytest tests/` |
| **`schema`** | Generates a markdown formatted schema diagram and writes it to **`SCHEMA.md`**. | `uv run dotenv run python -m src.generate_schema > SCHEMA.md` |
| **`erd`** | Generates a mermaid Entity-Relationship Diagram of the database and outputs to **`ERD.md`**. | `uv run dotenv run python -m src.generate_erd` |
| **`psql`** | Starts an interactive psql DB session | `docker exec -it pot_postgres_db psql -U postgres -d POT_db` |
| **`kill-api`** | Kills the API server running on port 8080 <br> Because `just populate` starts the api in the background for ease-of-use. | `uv run -m src.scripts.kill-api` |