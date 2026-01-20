from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from .. import schemas
from ..database import get_db_session
from ..domains.authentication import (
    Role,
    require_role,
    get_password_hash,
    log_audit_event,
)
from ..models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(User).filter(User.email == user.email))
    db_user = result.scalar_one_or_none()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        role=user.role,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        event_type="user_create",
        details=f"User {current_user.email} created user {db_user.email}",
    )
    return db_user


@router.get("/", response_model=List[schemas.UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(Role.SUPERVISOR)),
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=schemas.UserRead)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(Role.SUPERVISOR)),
):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return db_user


@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user(
    user_id: int,
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    db_user.email = user.email
    db_user.name = user.name
    if user.password:
        db_user.hashed_password = get_password_hash(user.password)
    db_user.role = user.role
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await db.delete(db_user)
    await db.commit()
    return
