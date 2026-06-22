from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alerts import AlertListResponse, AlertResponse, AlertUpdate
from app.api.v1.auth import get_current_user_id
from app.api.v1.deps import verify_farm_access

router = APIRouter(
    prefix="/farms/{farm_id}/alerts",
    tags=["Alerts"],
    dependencies=[Depends(verify_farm_access)],
)


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    farm_id: UUID,
    is_read: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None, alias="type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    filters = {"farm_id": farm_id}
    if is_read is not None:
        filters["is_read"] = is_read
    if severity:
        filters["severity"] = severity
    if alert_type:
        filters["type"] = alert_type

    from app.repositories.base import BaseRepository
    repo = BaseRepository(Alert, session)

    total = await repo.count(filters=filters)
    alerts = await repo.get_multi(
        skip=skip,
        limit=limit,
        filters=filters,
        order_by="created_at",
        descending=True,
    )

    return AlertListResponse(
        total=total,
        items=[AlertResponse.model_validate(a) for a in alerts],
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    farm_id: UUID,
    alert_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    from app.repositories.base import BaseRepository
    repo = BaseRepository(Alert, session)
    alert = await repo.get(alert_id)
    if alert is None or alert.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ogohlantirish topilmadi.")
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    farm_id: UUID,
    alert_id: UUID,
    request: AlertUpdate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    from app.repositories.base import BaseRepository
    repo = BaseRepository(Alert, session)
    existing = await repo.get(alert_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ogohlantirish topilmadi.")

    alert = await repo.update(alert_id, request)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ogohlantirish topilmadi.")
    return alert


@router.post("/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_as_read(
    farm_id: UUID,
    alert_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    from app.repositories.base import BaseRepository
    repo = BaseRepository(Alert, session)
    existing = await repo.get(alert_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ogohlantirish topilmadi.")

    alert = await repo.update_by_dict(alert_id, {"is_read": True})
    return alert


@router.post("/read-all")
async def mark_all_alerts_as_read(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        update(Alert)
        .where(Alert.farm_id == farm_id)
        .values(is_read=True)
    )
    result = await session.execute(stmt)
    await session.flush()
    return {"updated": result.rowcount}


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    farm_id: UUID,
    alert_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    from app.repositories.base import BaseRepository
    repo = BaseRepository(Alert, session)
    existing = await repo.get(alert_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ogohlantirish topilmadi.")

    await repo.delete(alert_id)
