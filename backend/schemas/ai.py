from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ParsedOperation(BaseModel):
    operation_type: str = Field(
        ...,
        pattern=r"^(production|consumption|purchase|expense)$",
    )
    record_type: Optional[str] = None
    animal_id: Optional[str] = None
    group_id: Optional[str] = None
    item_name: Optional[str] = None
    item_category: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    amount: Optional[Decimal] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_operation(self) -> "ParsedOperation":
        if self.operation_type == "production":
            if not self.record_type:
                raise ValueError("record_type is required for production operations.")
            if self.quantity is None:
                raise ValueError("quantity is required for production operations.")
        if self.operation_type == "consumption":
            if not self.item_name:
                raise ValueError("item_name is required for consumption operations.")
            if self.quantity is None:
                raise ValueError("quantity is required for consumption operations.")
        return self


class ParseEntryRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language text from farmer describing farm operations.",
    )
    farm_id: Optional[str] = Field(
        None,
        description="Optional farm UUID to give the AI parser farm-specific context.",
    )


class ParseEntryResponse(BaseModel):
    entry_id: str
    operations: List[Dict[str, Any]]
    warnings: List[str]


class CommitEntryRequest(BaseModel):
    operations: List[ParsedOperation]


class CommitEntryResponse(BaseModel):
    success: bool
    committed_count: int
    errors: List[str] = Field(default_factory=list)


class AIAssistantRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Farmer's natural language question about farm analytics.",
    )
    farm_id: Optional[str] = None


class AIAssistantResponse(BaseModel):
    intent: str
    answer: str
    data: Optional[Any] = None


class IntentClassification(BaseModel):
    intent: str = Field(
        ...,
        pattern=r"^(profit_by_animal|milk_cost_per_liter|egg_cost_per_unit|"
        r"feed_remaining_days|production_trend|total_expenses|"
        r"total_revenue|animal_performance|inventory_summary|"
        r"general_question)$",
    )
    animal_type: Optional[str] = None
    time_period: Optional[str] = Field(
        None,
        pattern=r"^(today|yesterday|this_week|this_month|this_year|custom)$",
    )
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
