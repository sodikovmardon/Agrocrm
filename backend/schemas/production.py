from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductionRecordCreate(BaseModel):
    animal_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    type: str = Field(..., min_length=1, max_length=50)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)
    notes: Optional[str] = None
    recorded_at: datetime


class ProductionRecordResponse(BaseModel):
    id: UUID
    farm_id: UUID
    animal_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    type: str
    quantity: Decimal
    unit: str
    notes: Optional[str] = None
    recorded_at: datetime
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductionStatsQuery(BaseModel):
    farm_id: UUID
    type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    group_by: str = Field(default="day", pattern=r"^(day|week|month|year)$")
