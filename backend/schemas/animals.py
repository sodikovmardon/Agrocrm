from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnimalCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    tag_number: Optional[str] = Field(None, max_length=50)
    gender: str = Field(..., pattern=r"^(male|female)$")
    breed: Optional[str] = Field(None, max_length=255)
    birth_date: Optional[date] = None
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    current_weight: Optional[Decimal] = Field(None, ge=0)


class AnimalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tag_number: Optional[str] = Field(None, max_length=50)
    breed: Optional[str] = Field(None, max_length=255)
    current_weight: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern=r"^(active|sold|dead|slaughtered)$")


class AnimalResponse(BaseModel):
    id: UUID
    farm_id: UUID
    type: str
    name: str
    tag_number: Optional[str] = None
    gender: str
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    purchase_price: Optional[Decimal] = None
    current_weight: Optional[Decimal] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AnimalGroupCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    initial_count: int = Field(..., ge=1)
    current_count: int = Field(..., ge=0)
    average_weight: Optional[Decimal] = Field(None, ge=0)


class AnimalGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    current_count: Optional[int] = Field(None, ge=0)
    average_weight: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern=r"^(active|sold|dead|slaughtered)$")


class AnimalGroupResponse(BaseModel):
    id: UUID
    farm_id: UUID
    type: str
    name: str
    initial_count: int
    current_count: int
    average_weight: Optional[Decimal] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
