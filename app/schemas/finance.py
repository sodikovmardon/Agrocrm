from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.config import settings


INCOME_CATEGORIES = {"milk_sale", "egg_sale", "meat_sale", "animal_sale", "other_income"}
EXPENSE_CATEGORIES = {
    "feed",
    "medicine",
    "vaccine",
    "salary",
    "transport",
    "utilities",
    "equipment",
    "other_expense",
}


class FinanceTransactionCreate(BaseModel):
    type: str = Field(..., pattern=r"^(income|expense)$")
    category: str = Field(..., min_length=1, max_length=50)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default_factory=lambda: settings.DEFAULT_CURRENCY, max_length=10)
    description: Optional[str] = None
    animal_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    recorded_at: datetime


class FinanceTransactionResponse(BaseModel):
    id: UUID
    farm_id: UUID
    type: str
    category: str
    amount: Decimal
    currency: str
    description: Optional[str] = None
    animal_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    recorded_at: datetime
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryBreakdown(BaseModel):
    category: str
    total: float
    count: int


class FinanceSummaryResponse(BaseModel):
    farm_id: UUID
    period: str
    date_from: datetime
    date_to: datetime
    total_income: float
    total_expense: float
    net_profit: float
    currency: str
    income_by_category: List[CategoryBreakdown]
    expense_by_category: List[CategoryBreakdown]
