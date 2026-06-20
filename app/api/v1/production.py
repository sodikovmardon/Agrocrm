from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.production_repo import ProductionRepository
from app.schemas.production import ProductionRecordCreate, ProductionRecordResponse
from app.api.v1.auth import get_current_user_id
from app.api.v1.deps import verify_farm_access

router = APIRouter(
    prefix="/farms/{farm_id}/production",
    tags=["Production"],
    dependencies=[Depends(verify_farm_access)],
)


@router.post("", response_model=ProductionRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_production_record(
    farm_id: UUID,
    request: ProductionRecordCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = ProductionRepository(session)
    record = await repo.create(request, farm_id=farm_id, created_by=UUID(user_id))
    return record


@router.get("", response_model=List[ProductionRecordResponse])
async def list_production_records(
    farm_id: UUID,
    record_type: Optional[str] = Query(None, alias="type"),
    animal_id: Optional[UUID] = Query(None),
    group_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = ProductionRepository(session)
    records = await repo.get_records_by_farm(
        farm_id=farm_id,
        record_type=record_type,
        animal_id=animal_id,
        group_id=group_id,
        skip=skip,
        limit=limit,
    )
    return [ProductionRecordResponse.model_validate(r) for r in records]


@router.get("/{record_id}", response_model=ProductionRecordResponse)
async def get_production_record(
    farm_id: UUID,
    record_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = ProductionRepository(session)
    record = await repo.get(record_id)
    if record is None or record.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yozuv topilmadi.")
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_production_record(
    farm_id: UUID,
    record_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = ProductionRepository(session)
    existing = await repo.get(record_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yozuv topilmadi.")

    await repo.delete(record_id)
