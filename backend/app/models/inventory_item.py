"""InventoryItem ORM model."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant


class InventoryItem(TimestampMixin, Base):
    """An ingredient or supply tracked in a restaurant's inventory."""

    __tablename__ = "inventory_items"

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    ingredient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_on_hand: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reorder_threshold: Mapped[float | None] = mapped_column(Numeric(10, 2))
    unit_cost: Mapped[float | None] = mapped_column(Numeric(10, 2))
    expiry_date: Mapped[date | None] = mapped_column()
    supplier: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    restaurant: Mapped[Restaurant] = relationship(back_populates="inventory_items")
