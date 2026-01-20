from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db_session
from src.domains.authentication import require_role_async, Role
from src.models.species import Species
from src import schemas

router = APIRouter()


@router.get("/{species_id}", status_code=status.HTTP_200_OK)
async def read_species(
    species_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: schemas.UserRead = Depends(require_role_async(Role.OFFICER)),
):
    result = await db.execute(
        select(Species)
        .where(Species.id == species_id)
        .options(
            selectinload(Species.soil_textures),
            selectinload(Species.agroforestry_types),
        )
    )
    species = result.scalar_one_or_none()
    if species is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Species not found"
        )
    return species
