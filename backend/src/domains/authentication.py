from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .. import models, schemas
from ..config import settings
from ..database import get_db_session
from ..dependencies import get_current_active_user
from ..models.audit_log import AuditLog
import enum


# Define user roles
class Role(str, enum.Enum):
    OFFICER = "officer"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a new access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[models.User]:
    """Authenticates a user by email and password."""
    result = await db.execute(select(models.User).filter(models.User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_session)
) -> models.User:
    """Dependency to get the current user from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=user_id)
    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.execute(
        select(models.User).filter(models.User.id == token_data.id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user


role_hierarchy = {
    "officer": 1,
    "supervisor": 2,
    "admin": 3,
}


def require_role(required_role: Role):
    """Dependency to require a specific user role."""

    def role_checker(
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        """Checks if the current user has the required role."""
        user_role_level = role_hierarchy.get(current_user.role, 0)
        required_role_level = role_hierarchy.get(required_role.value, 0)

        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have adequate permissions.",
            )
        return current_user

    return role_checker


async def require_role_async(required_role: Role):
    """Async dependency to require a specific user role."""

    async def role_checker(
        current_user: schemas.UserRead = Depends(get_current_active_user),
    ) -> schemas.UserRead:
        """Checks if the current user has the required role."""
        user_role_level = role_hierarchy.get(current_user.role, 0)
        required_role_level = role_hierarchy.get(required_role.value, 0)

        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have adequate permissions.",
            )
        return current_user

    return role_checker


async def log_audit_event(
    db: AsyncSession,
    user_id: int,
    event_type: str,
    details: str,
):
    """
    Logs an audit event to the database.
    """
    db_log = AuditLog(user_id=user_id, event_type=event_type, details=details)
    db.add(db_log)
    await db.commit()
