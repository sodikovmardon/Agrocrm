from datetime import date
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[InventoryItem, Any, Any]):
    def __init__(self, session: AsyncSession):
        super().__init__(InventoryItem, session)

    async def get_items_by_farm(self, farm_id: UUID, category: Optional[str] = None) -> List[InventoryItem]:
        stmt = select(InventoryItem).where(InventoryItem.farm_id == farm_id)
        if category:
            stmt = stmt.where(InventoryItem.category == category)
        stmt = stmt.order_by(InventoryItem.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_item_by_name_and_farm(self, farm_id: UUID, name: str) -> Optional[InventoryItem]:
        stmt = select(InventoryItem).where(
            and_(InventoryItem.farm_id == farm_id, InventoryItem.name == name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_quantity(self, item_id: UUID, quantity_change: Decimal) -> Optional[InventoryItem]:
        from sqlalchemy import update

        item = await self.get(item_id)
        if item is None:
            return None
        new_quantity = item.current_quantity + quantity_change
        if new_quantity < 0:
            raise ValueError(f"Insufficient quantity for item '{item.name}'. Available: {item.current_quantity}, requested reduction: {abs(quantity_change)}.")
        stmt = (
            update(InventoryItem)
            .where(InventoryItem.id == item_id)
            .values(current_quantity=new_quantity)
            .returning(InventoryItem)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def reduce_quantity(self, item_id: UUID, quantity: Decimal) -> Optional[InventoryItem]:
        return await self.update_quantity(item_id, -quantity)

    async def increase_quantity(self, item_id: UUID, quantity: Decimal) -> Optional[InventoryItem]:
        return await self.update_quantity(item_id, quantity)

    async def get_items_low_stock(self, farm_id: UUID, threshold: Decimal = Decimal("10")) -> List[InventoryItem]:
        stmt = select(InventoryItem).where(
            and_(
                InventoryItem.farm_id == farm_id,
                InventoryItem.current_quantity <= threshold,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_items_expiring_soon(self, farm_id: UUID, within_days: int = 30) -> List[InventoryItem]:
        from datetime import timedelta, date

        target_date = date.today() + timedelta(days=within_days)
        stmt = select(InventoryItem).where(
            and_(
                InventoryItem.farm_id == farm_id,
                InventoryItem.expiry_date.isnot(None),
                InventoryItem.expiry_date <= target_date,
                InventoryItem.expiry_date >= date.today(),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_expired_items(self, farm_id: UUID) -> List[InventoryItem]:
        stmt = select(InventoryItem).where(
            and_(
                InventoryItem.farm_id == farm_id,
                InventoryItem.expiry_date.isnot(None),
                InventoryItem.expiry_date < date.today(),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_items_by_category(self, farm_id: UUID, category: str) -> List[InventoryItem]:
        stmt = select(InventoryItem).where(
            and_(InventoryItem.farm_id == farm_id, InventoryItem.category == category)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_inventory_value(self, farm_id: UUID) -> Decimal:
        stmt = select(func.sum(InventoryItem.current_quantity * InventoryItem.average_cost)).where(
            InventoryItem.farm_id == farm_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or Decimal("0.00")
