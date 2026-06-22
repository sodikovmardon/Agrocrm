import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductionRecord(Base):
    __tablename__ = "production_records"

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
    animal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("animals.id", ondelete="SET NULL"),
        nullable=True,
    )
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("animal_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    farm: Mapped["Farm"] = relationship(
        "Farm",
        back_populates="production_records",
        foreign_keys=[farm_id],
    )
    animal: Mapped[Optional["Animal"]] = relationship(
        "Animal",
        back_populates="production_records",
        foreign_keys=[animal_id],
    )
    group: Mapped[Optional["AnimalGroup"]] = relationship(
        "AnimalGroup",
        back_populates="production_records",
        foreign_keys=[group_id],
    )
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="production_records",
        foreign_keys=[created_by],
    )

    def __repr__(self) -> str:
        return f"<ProductionRecord(id={self.id}, type={self.type}, qty={self.quantity}, at={self.recorded_at})>"
