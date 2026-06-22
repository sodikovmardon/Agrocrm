import json
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import async_session_factory
from app.models.farm import Farm
from app.models.alert import Alert
from app.services.analytics_service import AnalyticsService
from app.ai.provider import llm_text_response


ALERT_LLM_PROMPT = """You are AgroSmart AI alert generator. 
Convert the following technical alert data into a short, impactful alert message in Uzbek language.
Alert data: {alert_data}

Respond with ONLY a JSON object:
{{
  "title": "Short alert title (max 100 chars)",
  "message": "Detailed alert message with specific numbers and recommendations (max 500 chars)"
}}"""


def run_async(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _generate_alert_title(alert_type: str, severity: str) -> str:
    titles = {
        "milk_drop": "Sut ishlab chiqarish keskin kamaydi",
        "feed_shortage": "Yem zaxirasi tugash arafasida",
        "item_expiry": "Mahsulot yaroqlilik muddati tugamoqda",
    }
    return titles.get(alert_type, "Ogohlantirish")


@celery_app.task(bind=True, name="app.tasks.alerts.detect_all_alerts")
def detect_all_alerts(self) -> Dict[str, Any]:
    async def _run():
        async with async_session_factory() as session:
            stmt = select(Farm.id).where(Farm.is_active == True)
            result = await session.execute(stmt)
            farm_ids = [row[0] for row in result.all()]

        all_alerts = []
        for farm_id in farm_ids:
            try:
                async with async_session_factory() as session:
                    service = AnalyticsService(session, farm_id)
                    detected = await service.detect_alerts()

                for alert_data in detected:
                    enhanced_alert = await _enhance_alert_with_llm(alert_data)
                    enhanced_alert["farm_id"] = str(farm_id)

                    async with async_session_factory() as session:
                        alert_entry = Alert(
                            farm_id=farm_id,
                            type=enhanced_alert["type"],
                            severity=enhanced_alert["severity"],
                            title=enhanced_alert["title"],
                            message=enhanced_alert["message"],
                            details=enhanced_alert.get("details", ""),
                        )
                        session.add(alert_entry)
                        await session.commit()
                        await session.refresh(alert_entry)
                        enhanced_alert["alert_id"] = str(alert_entry.id)

                    all_alerts.append(enhanced_alert)

            except Exception as e:
                all_alerts.append({
                    "farm_id": str(farm_id),
                    "error": str(e),
                })

        return {
            "status": "completed",
            "farms_checked": len(farm_ids),
            "alerts_created": len(all_alerts),
            "alerts": all_alerts,
        }

    return run_async(_run())


async def _enhance_alert_with_llm(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        prompt = ALERT_LLM_PROMPT.format(alert_data=json.dumps(alert_data, default=str, ensure_ascii=False))
        result = await llm_text_response(
            system_prompt="You are an alert generator. Respond with JSON only.",
            user_prompt=prompt,
            temperature=0.3,
        )
        enhanced = json.loads(result)
        alert_data["title"] = enhanced.get("title", alert_data.get("title", _generate_alert_title(alert_data.get("type", "unknown"), alert_data.get("severity", "info"))))
        alert_data["message"] = enhanced.get("message", alert_data.get("message", ""))
    except (json.JSONDecodeError, Exception):
        pass

    return alert_data


@celery_app.task(bind=True, name="app.tasks.alerts.detect_farm_alerts_single")
def detect_farm_alerts_single(self, farm_id_str: str) -> Dict[str, Any]:
    async def _run():
        farm_id = UUID(farm_id_str)
        async with async_session_factory() as session:
            service = AnalyticsService(session, farm_id)
            detected = await service.detect_alerts()

        alerts_created = []
        for alert_data in detected:
            enhanced = await _enhance_alert_with_llm(alert_data)
            enhanced["farm_id"] = str(farm_id)

            async with async_session_factory() as session:
                alert_entry = Alert(
                    farm_id=farm_id,
                    type=enhanced["type"],
                    severity=enhanced["severity"],
                    title=enhanced["title"],
                    message=enhanced["message"],
                    details=enhanced.get("details", ""),
                )
                session.add(alert_entry)
                await session.commit()
                await session.refresh(alert_entry)
                enhanced["alert_id"] = str(alert_entry.id)

            alerts_created.append(enhanced)

        return {
            "status": "completed",
            "alerts_created": len(alerts_created),
            "alerts": alerts_created,
        }

    return run_async(_run())
