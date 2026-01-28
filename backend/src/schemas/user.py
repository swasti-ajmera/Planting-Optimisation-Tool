from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
import enum


# User role definitions
# Roles define permission levels in the system with a hierarchical structure:
# - OFFICER (level 1): Basic user with limited permissions
# - SUPERVISOR (level 2): Can view and manage users and resources
# - ADMIN (level 3): Full system access, can create/update/delete all resources
class Role(str, enum.Enum):
    """Enumeration of user roles with hierarchical permissions."""

    OFFICER = "officer"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


# Base model for validation
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="The user's unique email address.")
    name: str = Field(..., description="The user's full name.")


# Used for registration (requires password input)
class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        description="The user's password (must be hashed before storage).",
    )
    role: str = "officer"


# This is what is returned after registration or when fetching the current user.
# NEVER INCLUDE PASSWORD
class UserRead(UserBase):
    id: int = Field(..., description="The unique database ID of the user.")
    role: str = Field(..., description="The user's role.")

    model_config = ConfigDict(from_attributes=True)


# Used for authentication requests
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Token (The contract for what the login endpoint returns)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for the JWT payload validation."""

    id: Optional[int] = None  # The user ID stored in the token's subject (sub) field
    role: Optional[str] = None
