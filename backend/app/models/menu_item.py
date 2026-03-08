"""MenuItem ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant


class MenuItem(TimestampMixin, Base):
    """A dish or drink on a restaurant's menu."""

    __tablename__ = "menu_items"

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    ingredient_cost: Mapped[float | None] = mapped_column(Numeric(10, 2))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    restaurant: Mapped[Restaurant] = relationship(back_populates="menu_items")
