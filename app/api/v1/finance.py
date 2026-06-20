from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.repositories.finance_repo import FinanceRepository
from app.schemas.finance import (
    CategoryBreakdown,
    FinanceSummaryResponse,
    FinanceTransactionCreate,
    FinanceTransactionResponse,
)
from app.api.v1.auth import get_current_user_id
from app.api.v1.deps import verify_farm_access

router = APIRouter(
    prefix="/farms/{farm_id}/finance",
    tags=["Finance"],
    dependencies=[Depends(verify_farm_access)],
)


def _resolve_period(
    time_period: str,
    date_from: Optional[datetime],
    date_to: Optional[datetime],
) -> tuple[datetime, datetime]:
    if date_from and date_to:
        return date_from, date_to

    today = datetime.now(timezone.utc)
    end = today

    if time_period == "today":
        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_period == "this_week":
        start = (today - timedelta(days=today.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif time_period == "this_year":
        start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # this_month (default) and 30-day fallback
        start = today - timedelta(days=30)

    return start, end


@router.post(
    "/transactions",
    response_model=FinanceTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    farm_id: UUID,
    request: FinanceTransactionCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = FinanceRepository(session)
    transaction = await repo.create(request, farm_id=farm_id, created_by=UUID(user_id))
    return transaction


@router.get("/transactions", response_model=List[FinanceTransactionResponse])
async def list_transactions(
    farm_id: UUID,
    tx_type: Optional[str] = Query(None, alias="type", pattern=r"^(income|expense)$"),
    category: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = FinanceRepository(session)
    transactions = await repo.get_transactions_by_farm(
        farm_id=farm_id,
        tx_type=tx_type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return [FinanceTransactionResponse.model_validate(t) for t in transactions]


@router.get("/transactions/{transaction_id}", response_model=FinanceTransactionResponse)
async def get_transaction(
    farm_id: UUID,
    transaction_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = FinanceRepository(session)
    transaction = await repo.get(transaction_id)
    if transaction is None or transaction.farm_id != farm_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tranzaksiya topilmadi.",
        )
    return transaction


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    farm_id: UUID,
    transaction_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    repo = FinanceRepository(session)
    existing = await repo.get(transaction_id)
    if existing is None or existing.farm_id != farm_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tranzaksiya topilmadi.",
        )
    await repo.delete(transaction_id)


@router.get("/summary", response_model=FinanceSummaryResponse)
async def get_finance_summary(
    farm_id: UUID,
    time_period: str = Query("this_month"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    start, end = _resolve_period(time_period, date_from, date_to)

    repo = FinanceRepository(session)
    total_income = await repo.get_total_by_type(farm_id, "income", start, end)
    total_expense = await repo.get_total_by_type(farm_id, "expense", start, end)
    income_breakdown = await repo.get_breakdown_by_category(farm_id, "income", start, end)
    expense_breakdown = await repo.get_breakdown_by_category(farm_id, "expense", start, end)

    return FinanceSummaryResponse(
        farm_id=farm_id,
        period=time_period,
        date_from=start,
        date_to=end,
        total_income=float(total_income),
        total_expense=float(total_expense),
        net_profit=float(total_income - total_expense),
        currency=settings.DEFAULT_CURRENCY,
        income_by_category=[CategoryBreakdown(**row) for row in income_breakdown],
        expense_by_category=[CategoryBreakdown(**row) for row in expense_breakdown],
    )
