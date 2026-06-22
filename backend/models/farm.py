import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    region: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    district: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
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

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="farms_owned",
        foreign_keys=[owner_id],
    )
    members: Mapped[List["FarmMember"]] = relationship(
        "FarmMember",
        back_populates="farm",
        cascade="all, delete-orphan",
    )
    animals: Mapped[List["Animal"]] = relationship(
        "Animal",
        back_populates="farm",
        cascade="all, delete-orphan",
    )
    animal_groups: Mapped[List["AnimalGroup"]] = relationship(
        "AnimalGroup",
        back_populates="farm",
        cascade="all, delete-orphan",
    )
    production_records: Mapped[List["ProductionRecord"]] = relationship(
        "ProductionRecord",
        back_populates="farm",
        cascade="all, delete-orphan",
        foreign_keys="ProductionRecord.farm_id",
    )
    inventory_items: Mapped[List["InventoryItem"]] = relationship(
        "InventoryItem",
        back_populates="farm",
        cascade="all, delete-orphan",
    )
    finance_transactions: Mapped[List["FinanceTransaction"]] = relationship(
        "FinanceTransaction",
        back_populates="farm",
        cascade="all, delete-orphan",
        foreign_keys="FinanceTransaction.farm_id",
    )

    def __repr__(self) -> str:
        return f"<Farm(id={self.id}, name={self.name}, region={self.region})>"


class FarmMember(Base):
    __tablename__ = "farm_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="worker",
    )
    permissions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    farm: Mapped["Farm"] = relationship(
        "Farm",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="farm_memberships",
    )

    def __repr__(self) -> str:
        return f"<FarmMember(id={self.id}, farm_id={self.farm_id}, user_id={self.user_id}, role={self.role})>"
