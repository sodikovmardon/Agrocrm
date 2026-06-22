from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.animal import Animal
from app.models.inventory import InventoryItem
from app.models.production import ProductionRecord
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.production_repo import ProductionRepository
from app.repositories.finance_repo import FinanceRepository


class AnalyticsService:
    def __init__(self, session: AsyncSession, farm_id: UUID):
        self.session = session
        self.farm_id = farm_id
        self.prod_repo = ProductionRepository(session)
        self.inv_repo = InventoryRepository(session)
        self.finance_repo = FinanceRepository(session)

    def _period_bounds(self, time_period: str) -> tuple[datetime, datetime]:
        today = datetime.now(timezone.utc)
        if time_period == "today":
            date_from = today.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "this_week":
            date_from = (today - timedelta(days=today.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif time_period == "this_year":
            date_from = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            date_from = today - timedelta(days=30)
        return date_from, today

    async def calculate_profit_by_animal(
        self,
        animal_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        if date_to is None:
            date_to = datetime.now(timezone.utc)
        if date_from is None:
            date_from = date_to - timedelta(days=30)

        stmt = select(Animal).where(
            and_(Animal.farm_id == self.farm_id, Animal.status == "active")
        )
        if animal_type:
            stmt = stmt.where(Animal.type == animal_type)
        result = await self.session.execute(stmt)
        animals = list(result.scalars().all())

        results = []
        for animal in animals:
            prod_sum = await self.prod_repo.get_total_production(
                farm_id=self.farm_id,
                record_type="milk",
                unit="liter",
                date_from=date_from,
                date_to=date_to,
            )
            revenue = Decimal("0")
            cost = Decimal("0")

            if animal.type == "cow":
                milk_price_per_liter = Decimal("5000")
                revenue = prod_sum * milk_price_per_liter

            feed_cost = await self._calculate_feed_cost(animal.id, date_from, date_to)
            total_cost = (animal.purchase_price or Decimal("0")) / Decimal("365") * Decimal("30") + feed_cost

            profit = revenue - total_cost
            results.append({
                "animal_id": str(animal.id),
                "animal_name": animal.name,
                "animal_type": animal.type,
                "tag_number": animal.tag_number,
                "revenue": float(revenue),
                "cost": float(total_cost),
                "profit": float(profit),
                "production_total": float(prod_sum),
            })

        results.sort(key=lambda x: x["profit"], reverse=True)
        return results

    async def calculate_milk_cost_per_liter(self) -> Dict[str, Any]:
        today = datetime.now(timezone.utc)
        date_from = today - timedelta(days=30)

        total_milk = await self.prod_repo.get_total_production(
            farm_id=self.farm_id,
            record_type="milk",
            unit="liter",
            date_from=date_from,
            date_to=today,
        )

        feed_items = await self.inv_repo.get_items_by_category(self.farm_id, "feed")
        total_feed_cost = Decimal("0")
        for item in feed_items:
            if item.average_cost:
                total_feed_cost += item.average_cost * item.current_quantity

        medicine_items = await self.inv_repo.get_items_by_category(self.farm_id, "medicine")
        total_medicine_cost = Decimal("0")
        for item in medicine_items:
            if item.average_cost:
                total_medicine_cost += item.average_cost * item.current_quantity

        stmt = select(func.count(Animal.id)).where(
            and_(Animal.farm_id == self.farm_id, Animal.type == "cow", Animal.status == "active")
        )
        result = await self.session.execute(stmt)
        active_cows = result.scalar_one() or 1

        labor_cost = Decimal("500000") * Decimal(str(active_cows))

        total_cost = total_feed_cost + total_medicine_cost + labor_cost

        cost_per_liter = float(total_cost / total_milk) if total_milk > 0 else 0

        return {
            "total_milk_liters": float(total_milk),
            "total_cost": float(total_cost),
            "cost_per_liter": cost_per_liter,
            "active_cows": active_cows,
            "feed_cost": float(total_feed_cost),
            "medicine_cost": float(total_medicine_cost),
            "labor_cost": float(labor_cost),
        }

    async def calculate_egg_cost_per_unit(self) -> Dict[str, Any]:
        today = datetime.now(timezone.utc)
        date_from = today - timedelta(days=30)

        total_eggs = await self.prod_repo.get_total_production(
            farm_id=self.farm_id,
            record_type="egg",
            unit="piece",
            date_from=date_from,
            date_to=today,
        )

        feed_items = await self.inv_repo.get_items_by_category(self.farm_id, "feed")
        total_feed_cost = Decimal("0")
        for item in feed_items:
            if item.average_cost:
                total_feed_cost += item.average_cost * item.current_quantity

        stmt = select(func.count(Animal.id)).where(
            and_(Animal.farm_id == self.farm_id, Animal.type == "chicken", Animal.status == "active")
        )
        result = await self.session.execute(stmt)
        active_chickens = result.scalar_one() or 1

        labor_cost = Decimal("200000") * Decimal(str(active_chickens)) / Decimal("10")

        total_cost = total_feed_cost + labor_cost
        cost_per_egg = float(total_cost / total_eggs) if total_eggs > 0 else 0

        return {
            "total_eggs": float(total_eggs),
            "total_cost": float(total_cost),
            "cost_per_egg": cost_per_egg,
            "active_chickens": active_chickens,
            "feed_cost": float(total_feed_cost),
            "labor_cost": float(labor_cost),
        }

    async def calculate_feed_remaining_days(self) -> Dict[str, Any]:
        feed_items = await self.inv_repo.get_items_by_category(self.farm_id, "feed")
        total_feed_quantity = Decimal("0")
        for item in feed_items:
            if item.unit == "kg":
                total_feed_quantity += item.current_quantity
            elif item.unit in ("sack", "bag", "qop"):
                total_feed_quantity += item.current_quantity * Decimal("25")

        today = datetime.now(timezone.utc)
        date_from = today - timedelta(days=7)
        consumption_records = await self.prod_repo.get_records_by_farm(
            farm_id=self.farm_id,
            record_type="consumption",
            date_from=date_from,
            date_to=today,
        )

        total_consumed_kg = Decimal("0")
        for record in consumption_records:
            if record.unit == "kg":
                total_consumed_kg += record.quantity
            elif record.unit in ("sack", "bag", "qop"):
                total_consumed_kg += record.quantity * Decimal("25")

        daily_consumption = total_consumed_kg / Decimal("7") if total_consumed_kg > 0 else Decimal("0")

        # No consumption data -> remaining_days is undefined (None), not infinity.
        # float("inf") is not JSON-serializable and crashes the response.
        if daily_consumption > 0:
            remaining_days = float(total_feed_quantity / daily_consumption)
            critical = remaining_days < settings.ALERT_FEED_DAYS_REMAINING
        else:
            remaining_days = None
            critical = False

        return {
            "total_feed_kg": float(total_feed_quantity),
            "daily_consumption_kg": float(daily_consumption),
            "remaining_days": remaining_days,
            "critical": critical,
        }

    async def get_production_trend(
        self,
        animal_type: Optional[str] = None,
        time_period: str = "this_month",
    ) -> Dict[str, Any]:
        today = datetime.now(timezone.utc)

        if time_period == "today":
            date_from = today.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "yesterday":
            date_from = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "this_week":
            date_from = today - timedelta(days=today.weekday())
            date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "this_year":
            date_from = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            date_from = today - timedelta(days=30)

        milk_data = await self.prod_repo.get_production_by_period(
            farm_id=self.farm_id,
            record_type="milk",
            unit="liter",
            date_from=date_from,
            date_to=today,
        )

        egg_data = await self.prod_repo.get_production_by_period(
            farm_id=self.farm_id,
            record_type="egg",
            unit="piece",
            date_from=date_from,
            date_to=today,
        )

        return {
            "period": time_period,
            "date_from": date_from.isoformat(),
            "date_to": today.isoformat(),
            "milk": milk_data,
            "eggs": egg_data,
        }

    async def calculate_total_expenses(
        self,
        time_period: str = "this_month",
    ) -> Dict[str, Any]:
        today = datetime.now(timezone.utc)
        date_from = today - timedelta(days=30)

        if time_period == "today":
            date_from = today.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "this_week":
            date_from = today - timedelta(days=today.weekday())
            date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "this_year":
            date_from = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        date_from, date_to = self._period_bounds(time_period)

        # Prefer real recorded finance transactions when available.
        recorded_expense = await self.finance_repo.get_total_by_type(
            self.farm_id, "expense", date_from, date_to
        )
        if recorded_expense > 0:
            breakdown = await self.finance_repo.get_breakdown_by_category(
                self.farm_id, "expense", date_from, date_to
            )
            return {
                "total_estimated_expenses": float(recorded_expense),
                "total_expenses": float(recorded_expense),
                "by_category": breakdown,
                "source": "finance_transactions",
                "period": time_period,
            }

        # Fallback estimate from inventory value + labor heuristic.
        inventory_items = await self.inv_repo.get_items_by_farm(self.farm_id)
        total_inventory_value = Decimal("0")
        for item in inventory_items:
            if item.average_cost:
                total_inventory_value += item.average_cost * item.current_quantity

        stmt = select(func.count(Animal.id)).where(
            and_(Animal.farm_id == self.farm_id, Animal.status == "active")
        )
        result = await self.session.execute(stmt)
        total_animals = result.scalar_one() or 0

        estimated_labor = Decimal("500000") * Decimal(max(total_animals // 5, 1))

        return {
            "inventory_cost": float(total_inventory_value),
            "estimated_labor_cost": float(estimated_labor),
            "total_estimated_expenses": float(total_inventory_value + estimated_labor),
            "total_expenses": float(total_inventory_value + estimated_labor),
            "source": "estimate",
            "period": time_period,
        }

    async def calculate_total_revenue(
        self,
        time_period: str = "this_month",
    ) -> Dict[str, Any]:
        today = datetime.now(timezone.utc)
        date_from = today - timedelta(days=30)

        if time_period == "today":
            date_from = today.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "this_week":
            date_from = today - timedelta(days=today.weekday())
            date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "this_year":
            date_from = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        total_milk = await self.prod_repo.get_total_production(
            farm_id=self.farm_id,
            record_type="milk",
            unit="liter",
            date_from=date_from,
            date_to=today,
        )

        total_eggs = await self.prod_repo.get_total_production(
            farm_id=self.farm_id,
            record_type="egg",
            unit="piece",
            date_from=date_from,
            date_to=today,
        )

        # Prefer real recorded sales income when available.
        recorded_income = await self.finance_repo.get_total_by_type(
            self.farm_id, "income", date_from, today
        )
        if recorded_income > 0:
            breakdown = await self.finance_repo.get_breakdown_by_category(
                self.farm_id, "income", date_from, today
            )
            return {
                "total_revenue": float(recorded_income),
                "by_category": breakdown,
                "milk_liters": float(total_milk),
                "egg_pieces": float(total_eggs),
                "source": "finance_transactions",
                "period": time_period,
            }

        # Fallback estimate using indicative market prices.
        milk_revenue = total_milk * Decimal("5000")
        egg_revenue = total_eggs * Decimal("800")

        return {
            "milk_revenue": float(milk_revenue),
            "egg_revenue": float(egg_revenue),
            "total_revenue": float(milk_revenue + egg_revenue),
            "milk_liters": float(total_milk),
            "egg_pieces": float(total_eggs),
            "source": "estimate",
            "period": time_period,
        }

    async def get_animal_performance(
        self,
        animal_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(Animal).where(
            and_(Animal.farm_id == self.farm_id, Animal.status == "active")
        )
        if animal_type:
            stmt = stmt.where(Animal.type == animal_type)
        result = await self.session.execute(stmt)
        animals = list(result.scalars().all())

        performance_data = []
        for animal in animals:
            prod_records = await self.prod_repo.get_production_by_animal(
                farm_id=self.farm_id,
                animal_id=animal.id,
                record_type="milk",
            )
            total_production = sum(float(r.quantity) for r in prod_records)

            performance_data.append({
                "animal_id": str(animal.id),
                "name": animal.name,
                "type": animal.type,
                "breed": animal.breed,
                "age_days": (datetime.now(timezone.utc).date() - animal.birth_date).days if animal.birth_date else None,
                "current_weight": float(animal.current_weight) if animal.current_weight else None,
                "total_milk_produced": total_production,
                "record_count": len(prod_records),
            })

        return performance_data

    async def get_inventory_summary(self) -> Dict[str, Any]:
        items = await self.inv_repo.get_items_by_farm(self.farm_id)
        low_stock = await self.inv_repo.get_items_low_stock(self.farm_id)
        expiring = await self.inv_repo.get_items_expiring_soon(self.farm_id)
        expired = await self.inv_repo.get_expired_items(self.farm_id)

        by_category: Dict[str, int] = {}
        for item in items:
            by_category[item.category] = by_category.get(item.category, 0) + 1

        return {
            "total_items": len(items),
            "by_category": by_category,
            "low_stock_items": [
                {"id": str(item.id), "name": item.name, "quantity": float(item.current_quantity)}
                for item in low_stock
            ],
            "expiring_items": [
                {"id": str(item.id), "name": item.name, "expiry_date": str(item.expiry_date)}
                for item in expiring
            ],
            "expired_items": [
                {"id": str(item.id), "name": item.name, "expiry_date": str(item.expiry_date)}
                for item in expired
            ],
        }

    async def _calculate_feed_cost(
        self,
        animal_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> Decimal:
        feed_items = await self.inv_repo.get_items_by_category(self.farm_id, "feed")
        total_cost = Decimal("0")
        for item in feed_items:
            if item.average_cost:
                total_cost += item.average_cost * item.current_quantity
        stmt = select(func.count(Animal.id)).where(
            and_(Animal.farm_id == self.farm_id, Animal.status == "active")
        )
        result = await self.session.execute(stmt)
        total_active = result.scalar_one() or 1
        return total_cost / Decimal(str(total_active))

    async def calculate_daily_metrics(self) -> Dict[str, Any]:
        today = datetime.now(timezone.utc)
        date_from = today - timedelta(days=1)

        total_milk = await self.prod_repo.get_total_production(
            farm_id=self.farm_id,
            record_type="milk",
            unit="liter",
            date_from=date_from,
            date_to=today,
        )

        total_eggs = await self.prod_repo.get_total_production(
            farm_id=self.farm_id,
            record_type="egg",
            unit="piece",
            date_from=date_from,
            date_to=today,
        )

        milk_cost = await self.calculate_milk_cost_per_liter()
        egg_cost = await self.calculate_egg_cost_per_unit()

        revenue = await self.calculate_total_revenue(time_period="today")
        expenses = await self.calculate_total_expenses(time_period="today")

        net_profit = revenue["total_revenue"] - expenses["total_estimated_expenses"]

        return {
            "farm_id": str(self.farm_id),
            "date": today.date().isoformat(),
            "total_milk_liters": float(total_milk),
            "total_eggs": float(total_eggs),
            "milk_cost_per_liter": milk_cost["cost_per_liter"],
            "egg_cost_per_unit": egg_cost["cost_per_egg"],
            "daily_revenue": revenue["total_revenue"],
            "daily_expenses": expenses["total_estimated_expenses"],
            "net_profit": net_profit,
        }

    async def detect_alerts(self) -> List[Dict[str, Any]]:
        alerts = []

        milk_trend = await self.prod_repo.get_daily_milk_production(self.farm_id, days=3)
        if len(milk_trend) >= 2:
            values = [m["total"] for m in milk_trend]
            if len(values) >= 2:
                drop_percent = ((values[0] - values[-1]) / values[-1]) * 100 if values[-1] > 0 else 0
                if drop_percent > 10:
                    from app.core.config import settings
                    if drop_percent > settings.ALERT_DAILY_MILK_DROP_PERCENT:
                        alerts.append({
                            "type": "milk_drop",
                            "severity": "warning",
                            "title": "Sut ishlab chiqarish kamaydi",
                            "message": f"So'nggi kunlarda sut ishlab chiqarish {drop_percent:.1f}% ga kamaydi.",
                            "details": f"Kunlik sut miqdori: {values[-1]:.1f} litr (oldingi: {values[0]:.1f} litr)",
                        })

        feed_status = await self.calculate_feed_remaining_days()
        if feed_status["critical"]:
            from app.core.config import settings
            alerts.append({
                "type": "feed_shortage",
                "severity": "critical",
                "title": "Yem zaxirasi tugamoqda",
                "message": f"Yem zaxirasi {feed_status['remaining_days']:.0f} kunga yetadi. Zudlik bilan yem sotib oling.",
                "details": f"Qolgan yem: {feed_status['total_feed_kg']:.1f} kg, kunlik sarf: {feed_status['daily_consumption_kg']:.1f} kg",
            })

        expiring_items = await self.inv_repo.get_items_expiring_soon(self.farm_id, within_days=30)
        for item in expiring_items:
            days_left = (item.expiry_date - datetime.now(timezone.utc).date()).days if item.expiry_date else 0
            if days_left is not None and days_left <= 30:
                alerts.append({
                    "type": "item_expiry",
                    "severity": "warning",
                    "title": f"'{item.name}' muddati tugamoqda",
                    "message": f"'{item.name}' mahsulotining yaroqlilik muddati {days_left} kundan keyin tugaydi.",
                    "details": f"Kategoriya: {item.category}, Miqdor: {item.current_quantity} {item.unit}, Muddati: {item.expiry_date}",
                })

        return alerts
