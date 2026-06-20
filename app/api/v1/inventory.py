from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.inventory_repo import InventoryRepository
from app.schemas.inventory import (
    InventoryConsumptionCreate,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
)
from app.api.v1.auth import get_current_user_id
from app.api.v1.deps import verify_farm_access

router = APIRouter(
    prefix="/farms/{farm_id}/inventory",
    tags=["Inventory"],
    dependencies=[Depends(verify_farm_access)],
)


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    farm_id: UUID,
    request: InventoryItemCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = InventoryRepository(session)
    item = await repo.create(request, farm_id=farm_id)
    return item


@router.get("", response_model=List[InventoryItemResponse])
async def list_inventory(
    farm_id: UUID,
    category: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = InventoryRepository(session)
    items = await repo.get_multi(
        skip=skip,
        limit=limit,
        filters={"farm_id": farm_id, "category": category} if category else {"farm_id": farm_id},
        order_by="name",
    )
    return [InventoryItemResponse.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    farm_id: UUID,
    item_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = InventoryRepository(session)
    item = await repo.get(item_id)
    if item is None or item.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventarizatsiya topilmadi.")
    return item


@router.put("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    farm_id: UUID,
    item_id: UUID,
    request: InventoryItemUpdate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = InventoryRepository(session)
    existing = await repo.get(item_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventarizatsiya topilmadi.")

    item = await repo.update(item_id, request)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventarizatsiya topilmadi.")
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    farm_id: UUID,
    item_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = InventoryRepository(session)
    existing = await repo.get(item_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventarizatsiya topilmadi.")

    await repo.delete(item_id)


@router.post("/consume", response_model=InventoryItemResponse)
async def consume_inventory(
    farm_id: UUID,
    request: InventoryConsumptionCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = InventoryRepository(session)
    existing = await repo.get(request.item_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventarizatsiya topilmadi.")

    try:
        item = await repo.reduce_quantity(request.item_id, request.quantity)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventarizatsiya topilmadi.")
    return item
