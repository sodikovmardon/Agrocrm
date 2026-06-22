import json
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import llm_structured_output, llm_text_response
from app.repositories.animal_repo import AnimalRepository
from app.repositories.farm_repo import FarmRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.production_repo import ProductionRepository
from app.services.analytics_service import AnalyticsService


INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a smart farm management system.
Given a farmer's question, classify it into one of these intents:

Intents:
- profit_by_animal: Question about which animal is most profitable, profit comparison between animals
- milk_cost_per_liter: Question about milk production cost per liter
- egg_cost_per_unit: Question about egg production cost per unit
- feed_remaining_days: Question about how many days feed will last
- production_trend: Question about production trends over time (increasing/decreasing)
- total_expenses: Question about total expenses over a period
- total_revenue: Question about total revenue from products
- animal_performance: Question about individual animal performance
- inventory_summary: Question about current inventory status, low stock items
- general_question: Questions that don't fit other categories (weather, general advice, etc.)

Respond with a JSON object:
{
  "intent": "profit_by_animal",
  "animal_type": null,
  "time_period": "this_month",
  "date_from": null,
  "date_to": null,
  "confidence": 0.95
}

Available time_period values: today, yesterday, this_week, this_month, this_year, custom
Use "custom" when user specifies exact dates, then provide date_from and date_to in YYYY-MM-DD format.
If no time period is mentioned, use this_month as default.
If an animal type is mentioned (cow, sheep, chicken), include it in animal_type field."""


async def process_assistant_question(
    question: str,
    user_id: UUID,
    farm_id: Optional[str],
    session: AsyncSession,
) -> Dict[str, Any]:
    intent_result = await classify_intent(question)

    intent = intent_result.get("intent", "general_question")
    confidence = intent_result.get("confidence", 0.0)

    if confidence < 0.3:
        intent = "general_question"

    resolved_farm_id = await resolve_farm_id(farm_id, user_id, session)
    if resolved_farm_id is None and intent != "general_question":
        return {
            "intent": intent,
            "answer": "Sizning profilingizda ferma topilmadi. Iltimos, avval ferma qo'shing.",
            "data": None,
        }

    analytics_service = AnalyticsService(session, resolved_farm_id)

    data = None
    try:
        if intent == "profit_by_animal":
            data = await analytics_service.calculate_profit_by_animal(
                animal_type=intent_result.get("animal_type"),
            )
        elif intent == "milk_cost_per_liter":
            data = await analytics_service.calculate_milk_cost_per_liter()
        elif intent == "egg_cost_per_unit":
            data = await analytics_service.calculate_egg_cost_per_unit()
        elif intent == "feed_remaining_days":
            data = await analytics_service.calculate_feed_remaining_days()
        elif intent == "production_trend":
            data = await analytics_service.get_production_trend(
                animal_type=intent_result.get("animal_type"),
                time_period=intent_result.get("time_period", "this_month"),
            )
        elif intent == "total_expenses":
            data = await analytics_service.calculate_total_expenses(
                time_period=intent_result.get("time_period", "this_month"),
            )
        elif intent == "total_revenue":
            data = await analytics_service.calculate_total_revenue(
                time_period=intent_result.get("time_period", "this_month"),
            )
        elif intent == "animal_performance":
            data = await analytics_service.get_animal_performance(
                animal_type=intent_result.get("animal_type"),
            )
        elif intent == "inventory_summary":
            data = await analytics_service.get_inventory_summary()
    except Exception as e:
        data = {"error": str(e)}

    answer = await generate_human_readable_response(
        question=question,
        intent=intent,
        data=data,
    )

    return {
        "intent": intent,
        "answer": answer,
        "data": data,
    }


async def classify_intent(question: str) -> Dict[str, Any]:
    result = await llm_structured_output(
        system_prompt=INTENT_CLASSIFICATION_PROMPT,
        user_prompt=question,
    )
    try:
        parsed = json.loads(result)
        required_keys = ["intent", "confidence"]
        for key in required_keys:
            if key not in parsed:
                return {"intent": "general_question", "confidence": 0.0}
        return parsed
    except (json.JSONDecodeError, TypeError):
        return {"intent": "general_question", "confidence": 0.0}


RESPONSE_GENERATION_PROMPT = """You are a helpful and knowledgeable AI farm assistant for AgroSmart AI.
A farmer asked a question, and we have retrieved the relevant data from the database.
Your job is to explain the data in a clear, friendly, and insightful way in Uzbek (O'zbek tilida).

The farmer's question: {question}
The intent of the question: {intent}
The data we retrieved: {data}

Provide:
1. A direct answer to the question based on the data.
2. Key insights or observations.
3. Practical recommendations if applicable.
4. Use numbers and comparisons where relevant.

Keep your response concise (2-4 paragraphs), warm, and professional. 
If the data contains errors or is empty, explain what data is missing."""


async def generate_human_readable_response(
    question: str,
    intent: str,
    data: Optional[Any],
) -> str:
    prompt = RESPONSE_GENERATION_PROMPT.format(
        question=question,
        intent=intent,
        data=json.dumps(data, default=str, ensure_ascii=False) if data else "Ma'lumot topilmadi.",
    )
    return await llm_text_response(
        system_prompt="Siz AgroSmart AI ning fermer yordamchisisiz. O'zbek tilida javob bering.",
        user_prompt=prompt,
    )


async def resolve_farm_id(farm_id: Optional[str], user_id: UUID, session: AsyncSession) -> Optional[UUID]:
    if farm_id:
        try:
            return UUID(farm_id)
        except (ValueError, AttributeError):
            pass
    farm_repo = FarmRepository(session)
    farms = await farm_repo.get_farms_by_owner(user_id)
    if not farms:
        return None
    return farms[0].id
