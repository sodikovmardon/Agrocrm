from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.animal_repo import AnimalRepository, AnimalGroupRepository
from app.schemas.animals import (
    AnimalCreate,
    AnimalGroupCreate,
    AnimalGroupResponse,
    AnimalGroupUpdate,
    AnimalResponse,
    AnimalUpdate,
)
from app.api.v1.auth import get_current_user_id
from app.api.v1.deps import verify_farm_access

router = APIRouter(
    prefix="/farms/{farm_id}/animals",
    tags=["Animals"],
    dependencies=[Depends(verify_farm_access)],
)


@router.post("", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
async def create_animal(
    farm_id: UUID,
    request: AnimalCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalRepository(session)
    animal = await repo.create(request, farm_id=farm_id)
    return animal


@router.get("", response_model=List[AnimalResponse])
async def list_animals(
    farm_id: UUID,
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalRepository(session)
    if status:
        animals = await repo.get_multi(
            skip=skip,
            limit=limit,
            filters={"farm_id": farm_id, "status": status},
            order_by="created_at",
            descending=True,
        )
    else:
        animals = await repo.get_multi(
            skip=skip,
            limit=limit,
            filters={"farm_id": farm_id},
            order_by="created_at",
            descending=True,
        )
    return [AnimalResponse.model_validate(a) for a in animals]


@router.get("/{animal_id}", response_model=AnimalResponse)
async def get_animal(
    farm_id: UUID,
    animal_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalRepository(session)
    animal = await repo.get(animal_id)
    if animal is None or animal.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hayvon topilmadi.")
    return animal


@router.put("/{animal_id}", response_model=AnimalResponse)
async def update_animal(
    farm_id: UUID,
    animal_id: UUID,
    request: AnimalUpdate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalRepository(session)
    existing = await repo.get(animal_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hayvon topilmadi.")

    animal = await repo.update(animal_id, request)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hayvon topilmadi.")
    return animal


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal(
    farm_id: UUID,
    animal_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalRepository(session)
    existing = await repo.get(animal_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hayvon topilmadi.")

    await repo.delete(animal_id)


group_router = APIRouter(
    prefix="/farms/{farm_id}/groups",
    tags=["Animal Groups"],
    dependencies=[Depends(verify_farm_access)],
)


@group_router.post("", response_model=AnimalGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    farm_id: UUID,
    request: AnimalGroupCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalGroupRepository(session)
    group = await repo.create(request, farm_id=farm_id)
    return group


@group_router.get("", response_model=List[AnimalGroupResponse])
async def list_groups(
    farm_id: UUID,
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalGroupRepository(session)
    groups = await repo.get_multi(
        skip=skip,
        limit=limit,
        filters={"farm_id": farm_id, "status": status} if status else {"farm_id": farm_id},
        order_by="created_at",
        descending=True,
    )
    return [AnimalGroupResponse.model_validate(g) for g in groups]


@group_router.get("/{group_id}", response_model=AnimalGroupResponse)
async def get_group(
    farm_id: UUID,
    group_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalGroupRepository(session)
    group = await repo.get(group_id)
    if group is None or group.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh topilmadi.")
    return group


@group_router.put("/{group_id}", response_model=AnimalGroupResponse)
async def update_group(
    farm_id: UUID,
    group_id: UUID,
    request: AnimalGroupUpdate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalGroupRepository(session)
    existing = await repo.get(group_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh topilmadi.")

    group = await repo.update(group_id, request)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh topilmadi.")
    return group


@group_router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    farm_id: UUID,
    group_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = AnimalGroupRepository(session)
    existing = await repo.get(group_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh topilmadi.")

    await repo.delete(group_id)
