from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AlertUpdate(BaseModel):
    is_read: Optional[bool] = None


class AlertResponse(BaseModel):
    id: UUID
    farm_id: UUID
    type: str
    severity: str
    title: str
    message: str
    details: Optional[str] = None
    is_read: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    total: int
    items: List[AlertResponse]
