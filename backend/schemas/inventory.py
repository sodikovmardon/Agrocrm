from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InventoryItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., pattern=r"^(feed|medicine|vaccine|product)$")
    unit: str = Field(..., min_length=1, max_length=20)
    current_quantity: Decimal = Field(default=0, ge=0)
    average_cost: Optional[Decimal] = Field(None, ge=0)
    expiry_date: Optional[date] = None


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, pattern=r"^(feed|medicine|vaccine|product)$")
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    current_quantity: Optional[Decimal] = Field(None, ge=0)
    average_cost: Optional[Decimal] = Field(None, ge=0)
    expiry_date: Optional[date] = None


class InventoryItemResponse(BaseModel):
    id: UUID
    farm_id: UUID
    name: str
    category: str
    unit: str
    current_quantity: Decimal
    average_cost: Optional[Decimal] = None
    expiry_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InventoryConsumptionCreate(BaseModel):
    item_id: UUID
    quantity: Decimal = Field(..., gt=0)
    notes: Optional[str] = None
