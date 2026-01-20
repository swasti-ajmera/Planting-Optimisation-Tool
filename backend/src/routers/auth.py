from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .. import schemas
from ..database import get_db_session
from ..domains.authentication import (
    Role,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    require_role,
)
from ..models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", response_model=schemas.user.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    user = await authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=schemas.user.UserRead)
async def register_user(
    user: schemas.user.UserCreate, db: AsyncSession = Depends(get_db_session)
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
    return db_user


@router.get("/users/me", response_model=schemas.user.UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users/me/items")
async def read_own_items(current_user: User = Depends(require_role(Role.ADMIN))):
    return [{"item_id": "Foo", "owner": current_user.name}]
