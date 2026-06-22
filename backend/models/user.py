import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="owner",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    farms_owned: Mapped[List["Farm"]] = relationship(
        "Farm",
        back_populates="owner",
        foreign_keys="Farm.owner_id",
    )
    farm_memberships: Mapped[List["FarmMember"]] = relationship(
        "FarmMember",
        back_populates="user",
    )
    production_records: Mapped[List["ProductionRecord"]] = relationship(
        "ProductionRecord",
        back_populates="created_by_user",
        foreign_keys="ProductionRecord.created_by",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, phone={self.phone}, role={self.role})>"
