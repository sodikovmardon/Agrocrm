from typing import Any, Dict, List
from uuid import UUID

from celery import chain, group
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.database import async_session_factory
from app.models.farm import Farm
from app.models.alert import Alert
from app.services.analytics_service import AnalyticsService
from app.ai.provider import llm_text_response


def run_async(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


ALERT_LLM_PROMPT = """You are AgroSmart AI alert generator. 
Convert the following technical alert data into a short, impactful alert message in Uzbek language.
Alert data: {alert_data}

Generate a JSON response:
{{
  "title": "Short alert title (max 100 chars)",
  "message": "Detailed alert message with specific numbers and recommendations (max 500 chars)"
}}"""


@celery_app.task(bind=True, name="app.tasks.analytics.calculate_daily_farm_metrics")
def calculate_daily_farm_metrics(self) -> Dict[str, Any]:
    async def _run():
        async with async_session_factory() as session:
            stmt = select(Farm.id).where(Farm.is_active == True)
            result = await session.execute(stmt)
            farm_ids = [row[0] for row in result.all()]

        results = []
        for farm_id in farm_ids:
            try:
                async with async_session_factory() as session:
                    service = AnalyticsService(session, farm_id)
                    metrics = await service.calculate_daily_metrics()
                    results.append(metrics)
            except Exception as e:
                results.append({
                    "farm_id": str(farm_id),
                    "error": str(e),
                })

        return {
            "status": "completed",
            "farms_processed": len(results),
            "results": results,
        }

    return run_async(_run())


@celery_app.task(bind=True, name="app.tasks.analytics.calculate_farm_metrics_single")
def calculate_farm_metrics_single(self, farm_id_str: str) -> Dict[str, Any]:
    async def _run():
        farm_id = UUID(farm_id_str)
        async with async_session_factory() as session:
            service = AnalyticsService(session, farm_id)
            metrics = await service.calculate_daily_metrics()
            return metrics

    return run_async(_run())
