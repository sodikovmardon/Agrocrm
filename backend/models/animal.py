import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import DateTime, Date, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Animal(Base):
    __tablename__ = "animals"

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
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    tag_number: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    gender: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    breed: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    birth_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    purchase_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    current_weight: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
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

    farm: Mapped["Farm"] = relationship(
        "Farm",
        back_populates="animals",
    )
    production_records: Mapped[List["ProductionRecord"]] = relationship(
        "ProductionRecord",
        back_populates="animal",
        foreign_keys="ProductionRecord.animal_id",
    )

    def __repr__(self) -> str:
        return f"<Animal(id={self.id}, tag={self.tag_number}, name={self.name}, status={self.status})>"


class AnimalGroup(Base):
    __tablename__ = "animal_groups"

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
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    initial_count: Mapped[int] = mapped_column(
        nullable=False,
    )
    current_count: Mapped[int] = mapped_column(
        nullable=False,
    )
    average_weight: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
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

    farm: Mapped["Farm"] = relationship(
        "Farm",
        back_populates="animal_groups",
    )
    production_records: Mapped[List["ProductionRecord"]] = relationship(
        "ProductionRecord",
        back_populates="group",
        foreign_keys="ProductionRecord.group_id",
    )

    def __repr__(self) -> str:
        return f"<AnimalGroup(id={self.id}, name={self.name}, type={self.type}, count={self.current_count})>"
