from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FarmMemberCreate(BaseModel):
    user_id: UUID
    role: str = Field(default="worker", pattern=r"^(owner|manager|worker)$")
    permissions: Dict[str, Any] = Field(default_factory=dict)


class FarmMemberResponse(BaseModel):
    id: UUID
    farm_id: UUID
    user_id: UUID
    role: str
    permissions: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class FarmCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    region: str = Field(..., min_length=1, max_length=255)
    district: str = Field(..., min_length=1, max_length=255)


class FarmUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    region: Optional[str] = Field(None, min_length=1, max_length=255)
    district: Optional[str] = Field(None, min_length=1, max_length=255)


class FarmResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    region: str
    district: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FarmDetailResponse(FarmResponse):
    members: List[FarmMemberResponse] = Field(default_factory=list)
    animal_count: int = 0
    group_count: int = 0
    inventory_count: int = 0


class FarmListResponse(BaseModel):
    total: int
    items: List[FarmResponse]
