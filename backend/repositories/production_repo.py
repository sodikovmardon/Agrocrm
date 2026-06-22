from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production import ProductionRecord
from app.repositories.base import BaseRepository


class ProductionRepository(BaseRepository[ProductionRecord, Any, Any]):
    def __init__(self, session: AsyncSession):
        super().__init__(ProductionRecord, session)

    async def get_records_by_farm(
        self,
        farm_id: UUID,
        record_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        animal_id: Optional[UUID] = None,
        group_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProductionRecord]:
        stmt = select(ProductionRecord).where(ProductionRecord.farm_id == farm_id)
        if record_type:
            stmt = stmt.where(ProductionRecord.type == record_type)
        if date_from:
            stmt = stmt.where(ProductionRecord.recorded_at >= date_from)
        if date_to:
            stmt = stmt.where(ProductionRecord.recorded_at <= date_to)
        if animal_id:
            stmt = stmt.where(ProductionRecord.animal_id == animal_id)
        if group_id:
            stmt = stmt.where(ProductionRecord.group_id == group_id)
        stmt = stmt.order_by(ProductionRecord.recorded_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_production(
        self,
        farm_id: UUID,
        record_type: str,
        unit: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(ProductionRecord.quantity), 0)).where(
            and_(
                ProductionRecord.farm_id == farm_id,
                ProductionRecord.type == record_type,
                ProductionRecord.unit == unit,
            )
        )
        if date_from:
            stmt = stmt.where(ProductionRecord.recorded_at >= date_from)
        if date_to:
            stmt = stmt.where(ProductionRecord.recorded_at <= date_to)
        result = await self.session.execute(stmt)
        return Decimal(str(result.scalar_one()))

    async def get_production_by_period(
        self,
        farm_id: UUID,
        record_type: str,
        unit: str,
        date_from: datetime,
        date_to: datetime,
    ) -> List[Dict[str, Any]]:
        stmt = select(
            func.date_trunc("day", ProductionRecord.recorded_at).label("date"),
            func.sum(ProductionRecord.quantity).label("total"),
        ).where(
            and_(
                ProductionRecord.farm_id == farm_id,
                ProductionRecord.type == record_type,
                ProductionRecord.unit == unit,
                ProductionRecord.recorded_at >= date_from,
                ProductionRecord.recorded_at <= date_to,
            )
        ).group_by(text("date")).order_by(text("date"))
        result = await self.session.execute(stmt)
        rows = result.all()
        return [{"date": str(row.date), "total": float(row.total)} for row in rows]

    async def get_daily_milk_production(self, farm_id: UUID, days: int = 3) -> List[Dict[str, Any]]:
        from datetime import timedelta, timezone

        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(
            func.date_trunc("day", ProductionRecord.recorded_at).label("date"),
            func.sum(ProductionRecord.quantity).label("total"),
        ).where(
            and_(
                ProductionRecord.farm_id == farm_id,
                ProductionRecord.type == "milk",
                ProductionRecord.unit == "liter",
                ProductionRecord.recorded_at >= since,
            )
        ).group_by(text("date")).order_by(text("date"))
        result = await self.session.execute(stmt)
        rows = result.all()
        return [{"date": str(row.date), "total": float(row.total)} for row in rows]

    async def get_production_by_animal(
        self,
        farm_id: UUID,
        animal_id: UUID,
        record_type: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[ProductionRecord]:
        stmt = select(ProductionRecord).where(
            and_(
                ProductionRecord.farm_id == farm_id,
                ProductionRecord.animal_id == animal_id,
                ProductionRecord.type == record_type,
            )
        )
        if date_from:
            stmt = stmt.where(ProductionRecord.recorded_at >= date_from)
        if date_to:
            stmt = stmt.where(ProductionRecord.recorded_at <= date_to)
        stmt = stmt.order_by(ProductionRecord.recorded_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
