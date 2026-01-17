from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum
import os
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

# ======================
# Configuration
# ======================
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# PostgreSQL Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/POT_db")

# SQLAlchemy Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ======================
# Database Models
# ======================
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="officer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_email = Column(String, nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Create tables
Base.metadata.create_all(bind=engine)

# ======================
# Database Dependency
# ======================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================
# Enums
# ======================
class UserRole(str, Enum):
    OFFICER = "officer"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

class AuditAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    TOKEN_REFRESH = "token_refresh"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"

# ======================
# Pydantic Schemas
# ======================
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.OFFICER

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    user_email: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    details: Optional[dict]
    created_at: str

    class Config:
        from_attributes = True

# ======================
# Security
# ======================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ======================
# Audit Logging Functions
# ======================
def log_audit(
    db: Session,
    action: AuditAction,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    details: Optional[dict] = None
):
    """Log audit event to database"""
    try:
        audit_log = AuditLog(
            user_id=uuid.UUID(user_id) if user_id else None,
            user_email=user_email,
            action=action.value,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details=details
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"Error logging audit: {e}")
        db.rollback()

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"

def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")

# ======================
# Database Functions
# ======================
def get_user_by_email(db: Session, email: str):
    """Get user from database by email"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, full_name: str, password: str, role: str = UserRole.OFFICER):
    """Create new user in database"""
    try:
        db_user = User(
            email=email,
            full_name=full_name,
            password=password,
            role=role,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

def update_last_login(db: Session, email: str):
    """Update user's last login timestamp"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.last_login = datetime.utcnow()
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error updating last login: {e}")

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    if not user:
        return False
    if user.password != password:
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        role: str = payload.get("role")
        
        if email is None or token_type != "access":
            raise credentials_exception
        token_data = TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

# ======================
# Role-Based Access Control
# ======================
def require_role(allowed_roles: List[UserRole]):
    """Dependency to check if user has required role"""
    async def role_checker(current_user: User = Depends(get_current_user), request: Request = None, db: Session = Depends(get_db)):
        user_role = current_user.role
        if user_role not in [role.value for role in allowed_roles]:
            if request:
                log_audit(
                    db=db,
                    action=AuditAction.ACCESS_DENIED,
                    user_id=str(current_user.id),
                    user_email=current_user.email,
                    resource_type="endpoint",
                    resource_id=request.url.path,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    status="denied",
                    details={"required_roles": [role.value for role in allowed_roles], "user_role": user_role}
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        
        if request:
            log_audit(
                db=db,
                action=AuditAction.ACCESS_GRANTED,
                user_id=str(current_user.id),
                user_email=current_user.email,
                resource_type="endpoint",
                resource_id=request.url.path,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                status="success",
                details={"user_role": user_role}
            )
        return current_user
    return role_checker

def require_admin():
    return require_role([UserRole.ADMIN])

def require_supervisor_or_admin():
    return require_role([UserRole.SUPERVISOR, UserRole.ADMIN])

def require_any_role():
    return require_role([UserRole.OFFICER, UserRole.SUPERVISOR, UserRole.ADMIN])

# ======================
# FastAPI App
# ======================
app = FastAPI(title="POT Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# Routes
# ======================

@app.get("/")
async def root():
    return {
        "message": "POT Backend API - Planting Optimisation Tool",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        log_audit(
            db=db,
            action=AuditAction.REGISTER,
            user_email=user.email,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status="failed",
            details={"reason": "Email already registered"}
        )
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = create_user(db, user.email, user.full_name, user.password, user.role.value)
    
    log_audit(
        db=db,
        action=AuditAction.REGISTER,
        user_id=str(db_user.id),
        user_email=db_user.email,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        status="success",
        details={"role": db_user.role}
    )
    
    return UserResponse(
        id=str(db_user.id),
        email=db_user.email,
        full_name=db_user.full_name,
        role=db_user.role,
        created_at=db_user.created_at.isoformat()
    )

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        log_audit(
            db=db,
            action=AuditAction.LOGIN,
            user_email=form_data.username,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status="failed",
            details={"reason": "Invalid credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    update_last_login(db, user.email)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, 
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role})
    
    log_audit(
        db=db,
        action=AuditAction.LOGIN,
        user_id=str(user.id),
        user_email=user.email,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        status="success",
        details={"role": user.role}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str, request: Request = None, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        role: str = payload.get("role")
        
        if email is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        log_audit(
            db=db,
            action=AuditAction.TOKEN_REFRESH,
            ip_address=get_client_ip(request) if request else None,
            user_agent=get_user_agent(request) if request else None,
            status="failed",
            details={"reason": "Invalid token"}
        )
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, 
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role})
    
    log_audit(
        db=db,
        action=AuditAction.TOKEN_REFRESH,
        user_id=str(user.id),
        user_email=user.email,
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None,
        status="success"
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        created_at=current_user.created_at.isoformat()
    )

@app.get("/admin/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    current_user: User = Depends(require_admin()),
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get audit logs (Admin only)"""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
    return [AuditLogResponse(
        id=str(log.id),
        user_id=str(log.user_id) if log.user_id else None,
        user_email=log.user_email,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        status=log.status,
        details=log.details,
        created_at=log.created_at.isoformat()
    ) for log in logs]

@app.get("/admin/audit-logs/user/{user_email}")
async def get_user_audit_logs(
    user_email: str,
    current_user: User = Depends(require_admin()),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get audit logs for specific user (Admin only)"""
    logs = db.query(AuditLog).filter(AuditLog.user_email == user_email).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [AuditLogResponse(
        id=str(log.id),
        user_id=str(log.user_id) if log.user_id else None,
        user_email=log.user_email,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        status=log.status,
        details=log.details,
        created_at=log.created_at.isoformat()
    ) for log in logs]

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    """Example protected route - requires authentication"""
    return {
        "message": f"Hello {current_user.full_name}! This is a protected route.",
        "email": current_user.email,
        "role": current_user.role
    }

@app.get("/officer/dashboard")
async def officer_dashboard(current_user: User = Depends(require_any_role()), request: Request = None):
    """Officer dashboard - accessible by all authenticated users"""
    return {
        "message": "Officer Dashboard",
        "user": current_user.full_name,
        "role": current_user.role
    }

@app.get("/supervisor/reports")
async def supervisor_reports(current_user: User = Depends(require_supervisor_or_admin()), request: Request = None):
    """Supervisor reports - accessible by supervisors and admins only"""
    return {
        "message": "Supervisor Reports",
        "user": current_user.full_name,
        "role": current_user.role
    }

@app.get("/admin/users")
async def admin_users(current_user: User = Depends(require_admin()), request: Request = None):
    """Admin panel - accessible by admins only"""
    return {
        "message": "Admin User Management",
        "user": current_user.full_name,
        "role": current_user.role
    }

@app.get("/admin/settings")
async def admin_settings(current_user: User = Depends(require_admin()), request: Request = None):
    """Admin settings - accessible by admins only"""
    return {
        "message": "Admin Settings",
        "user": current_user.full_name,
        "role": current_user.role
    }

# ======================
# Run with: uv run uvicorn main:app --reload
# ======================