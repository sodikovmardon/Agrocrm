from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.analytics_service import AnalyticsService
from app.api.v1.auth import get_current_user_id
from app.api.v1.deps import verify_farm_access

router = APIRouter(
    prefix="/farms/{farm_id}/analytics",
    tags=["Analytics"],
    dependencies=[Depends(verify_farm_access)],
)


@router.get("/profit-by-animal")
async def get_profit_by_animal(
    farm_id: UUID,
    animal_type: str = Query(None),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    results = await service.calculate_profit_by_animal(animal_type=animal_type)
    return {"data": results}


@router.get("/milk-cost-per-liter")
async def get_milk_cost_per_liter(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    result = await service.calculate_milk_cost_per_liter()
    return result


@router.get("/egg-cost-per-unit")
async def get_egg_cost_per_unit(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    result = await service.calculate_egg_cost_per_unit()
    return result


@router.get("/feed-remaining-days")
async def get_feed_remaining_days(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    result = await service.calculate_feed_remaining_days()
    return result


@router.get("/production-trend")
async def get_production_trend(
    farm_id: UUID,
    animal_type: str = Query(None),
    time_period: str = Query("this_month"),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    result = await service.get_production_trend(animal_type=animal_type, time_period=time_period)
    return result


@router.get("/revenue")
async def get_revenue(
    farm_id: UUID,
    time_period: str = Query("this_month"),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    result = await service.calculate_total_revenue(time_period=time_period)
    return result


@router.get("/expenses")
async def get_expenses(
    farm_id: UUID,
    time_period: str = Query("this_month"),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    result = await service.calculate_total_expenses(time_period=time_period)
    return result


@router.get("/animal-performance")
async def get_animal_performance(
    farm_id: UUID,
    animal_type: str = Query(None),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    result = await service.get_animal_performance(animal_type=animal_type)
    return {"data": result}


@router.get("/inventory-summary")
async def get_inventory_summary(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    result = await service.get_inventory_summary()
    return result


@router.get("/daily-metrics")
async def get_daily_metrics(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(session, farm_id)
    result = await service.calculate_daily_metrics()
    return result
