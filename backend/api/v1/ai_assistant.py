from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import check_rate_limit
from app.schemas.ai import AIAssistantRequest, AIAssistantResponse
from app.services.ai_assistant_service import process_assistant_question
from app.api.v1.auth import get_current_user_id

router = APIRouter(prefix="/ai/assistant", tags=["AI Assistant"])


@router.post("/ask", response_model=AIAssistantResponse)
async def ask_ai_assistant(
    request: AIAssistantRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    rate_info = await check_rate_limit(f"assistant:{user_id}")
    if not rate_info["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"So'rovlar chegarasidan oshib ketdingiz. {rate_info['remaining']} so'rov qoldi.",
        )

    result = await process_assistant_question(
        question=request.question,
        user_id=UUID(user_id),
        farm_id=request.farm_id,
        session=session,
    )

    return AIAssistantResponse(
        intent=result["intent"],
        answer=result["answer"],
        data=result.get("data"),
    )
