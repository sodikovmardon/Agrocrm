from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import check_rate_limit
from app.schemas.ai import (
    CommitEntryRequest,
    CommitEntryResponse,
    ParseEntryRequest,
    ParseEntryResponse,
)
from app.services.ai_parser_service import commit_parsed_entry, parse_farmer_text
from app.api.v1.auth import get_current_user_id

router = APIRouter(prefix="/ai/entries", tags=["AI Parser"])


@router.post("/parse", response_model=ParseEntryResponse)
async def parse_entry(
    request: ParseEntryRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    rate_info = await check_rate_limit(f"parse:{user_id}")
    if not rate_info["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"So'rovlar chegarasidan oshib ketdingiz. {rate_info['remaining']} so'rov qoldi.",
        )

    result = await parse_farmer_text(
        text=request.text,
        session=session,
        farm_id=request.farm_id,
    )

    return ParseEntryResponse(
        entry_id=result["entry_id"],
        operations=result["operations"],
        warnings=result["warnings"],
    )


@router.post("/{entry_id}/commit", response_model=CommitEntryResponse)
async def commit_entry(
    entry_id: str,
    request: CommitEntryRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await commit_parsed_entry(
        entry_id=entry_id,
        operations=[op.model_dump() for op in request.operations],
        user_id=UUID(user_id),
        session=session,
    )

    return CommitEntryResponse(
        success=result["success"],
        committed_count=result["committed_count"],
        errors=result["errors"],
    )
