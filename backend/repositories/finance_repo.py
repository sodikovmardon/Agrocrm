from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import FinanceTransaction
from app.repositories.base import BaseRepository


class FinanceRepository(BaseRepository[FinanceTransaction, Any, Any]):
    def __init__(self, session: AsyncSession):
        super().__init__(FinanceTransaction, session)

    async def get_transactions_by_farm(
        self,
        farm_id: UUID,
        tx_type: Optional[str] = None,
        category: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FinanceTransaction]:
        stmt = select(FinanceTransaction).where(FinanceTransaction.farm_id == farm_id)
        if tx_type:
            stmt = stmt.where(FinanceTransaction.type == tx_type)
        if category:
            stmt = stmt.where(FinanceTransaction.category == category)
        if date_from:
            stmt = stmt.where(FinanceTransaction.recorded_at >= date_from)
        if date_to:
            stmt = stmt.where(FinanceTransaction.recorded_at <= date_to)
        stmt = stmt.order_by(FinanceTransaction.recorded_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_by_type(
        self,
        farm_id: UUID,
        tx_type: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
            and_(
                FinanceTransaction.farm_id == farm_id,
                FinanceTransaction.type == tx_type,
            )
        )
        if date_from:
            stmt = stmt.where(FinanceTransaction.recorded_at >= date_from)
        if date_to:
            stmt = stmt.where(FinanceTransaction.recorded_at <= date_to)
        result = await self.session.execute(stmt)
        return Decimal(str(result.scalar_one()))

    async def get_breakdown_by_category(
        self,
        farm_id: UUID,
        tx_type: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(
            FinanceTransaction.category.label("category"),
            func.sum(FinanceTransaction.amount).label("total"),
            func.count(FinanceTransaction.id).label("count"),
        ).where(
            and_(
                FinanceTransaction.farm_id == farm_id,
                FinanceTransaction.type == tx_type,
            )
        )
        if date_from:
            stmt = stmt.where(FinanceTransaction.recorded_at >= date_from)
        if date_to:
            stmt = stmt.where(FinanceTransaction.recorded_at <= date_to)
        stmt = stmt.group_by(FinanceTransaction.category).order_by(
            func.sum(FinanceTransaction.amount).desc()
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {"category": row.category, "total": float(row.total), "count": int(row.count)}
            for row in rows
        ]

    async def get_total_by_category(
        self,
        farm_id: UUID,
        category: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
            and_(
                FinanceTransaction.farm_id == farm_id,
                FinanceTransaction.category == category,
            )
        )
        if date_from:
            stmt = stmt.where(FinanceTransaction.recorded_at >= date_from)
        if date_to:
            stmt = stmt.where(FinanceTransaction.recorded_at <= date_to)
        result = await self.session.execute(stmt)
        return Decimal(str(result.scalar_one()))
