from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.farm_repo import FarmRepository
from app.repositories.animal_repo import AnimalRepository, AnimalGroupRepository
from app.repositories.inventory_repo import InventoryRepository
from app.schemas.farms import (
    FarmCreate,
    FarmDetailResponse,
    FarmListResponse,
    FarmMemberCreate,
    FarmMemberResponse,
    FarmResponse,
    FarmUpdate,
)
from app.api.v1.auth import get_current_user_id, get_current_user_role
from app.api.v1.deps import verify_farm_access

router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    request: FarmCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = FarmRepository(session)
    farm = await repo.create(request, owner_id=UUID(user_id))
    return farm


@router.get("", response_model=FarmListResponse)
async def list_farms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = FarmRepository(session)
    uid = UUID(user_id)

    owned = await repo.get_farms_by_owner(uid)
    member = await repo.get_farms_by_member(uid)

    seen = set()
    all_farms = []
    for f in owned + member:
        if f.id not in seen:
            seen.add(f.id)
            all_farms.append(f)

    total = len(all_farms)
    items = all_farms[skip:skip + limit]
    return FarmListResponse(total=total, items=[FarmResponse.model_validate(f) for f in items])


@router.get("/{farm_id}", response_model=FarmDetailResponse)
async def get_farm(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    _: UUID = Depends(verify_farm_access),
    session: AsyncSession = Depends(get_db),
):
    repo = FarmRepository(session)
    farm = await repo.get_farm_with_members(farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ferma topilmadi.")

    animal_repo = AnimalRepository(session)
    group_repo = AnimalGroupRepository(session)
    inv_repo = InventoryRepository(session)

    animal_count = await animal_repo.get_active_animal_count(farm_id)
    group_count = await group_repo.get_active_group_count(farm_id)
    inventory_count = await inv_repo.count(filters={"farm_id": farm_id})

    response = FarmDetailResponse(
        id=farm.id,
        owner_id=farm.owner_id,
        name=farm.name,
        region=farm.region,
        district=farm.district,
        is_active=farm.is_active,
        created_at=farm.created_at,
        updated_at=farm.updated_at,
        members=[FarmMemberResponse.model_validate(m) for m in farm.members],
        animal_count=animal_count,
        group_count=group_count,
        inventory_count=inventory_count,
    )
    return response


@router.put("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: UUID,
    request: FarmUpdate,
    user_id: str = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    _: UUID = Depends(verify_farm_access),
    session: AsyncSession = Depends(get_db),
):
    if role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat egasi yoki admin ferma ma'lumotlarini o'zgartirishi mumkin.",
        )

    repo = FarmRepository(session)
    farm = await repo.update(farm_id, request)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ferma topilmadi.")
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farm(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    _: UUID = Depends(verify_farm_access),
    session: AsyncSession = Depends(get_db),
):
    if role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat egasi fermani o'chirishi mumkin.",
        )

    repo = FarmRepository(session)
    deleted = await repo.delete(farm_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ferma topilmadi.")


@router.post("/{farm_id}/members", response_model=FarmMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_farm_member(
    farm_id: UUID,
    request: FarmMemberCreate,
    user_id: str = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    _: UUID = Depends(verify_farm_access),
    session: AsyncSession = Depends(get_db),
):
    if role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat egasi yoki admin a'zo qo'shishi mumkin.",
        )

    repo = FarmRepository(session)
    member = await repo.add_member(
        farm_id=farm_id,
        user_id=request.user_id,
        role=request.role,
        permissions=request.permissions,
    )
    return member


@router.delete("/{farm_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_farm_member(
    farm_id: UUID,
    member_user_id: UUID,
    user_id: str = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    _: UUID = Depends(verify_farm_access),
    session: AsyncSession = Depends(get_db),
):
    if role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat egasi yoki admin a'zoni o'chirishi mumkin.",
        )

    repo = FarmRepository(session)
    removed = await repo.remove_member(farm_id, member_user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="A'zo topilmadi.")


@router.get("/{farm_id}/members", response_model=List[FarmMemberResponse])
async def list_farm_members(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    _: UUID = Depends(verify_farm_access),
    session: AsyncSession = Depends(get_db),
):
    repo = FarmRepository(session)
    members = await repo.get_members(farm_id)
    return [FarmMemberResponse.model_validate(m) for m in members]
