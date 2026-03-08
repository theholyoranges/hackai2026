"""SalesRecord ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem
    from app.models.restaurant import Restaurant


class SalesRecord(Base):
    """A single sales transaction line item."""

    __tablename__ = "sales_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(100))
    sale_date: Mapped[datetime] = mapped_column(nullable=False)
    day_of_week: Mapped[str | None] = mapped_column(String(10))
    hour_of_day: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    restaurant: Mapped[Restaurant] = relationship(back_populates="sales_records")
    menu_item: Mapped[MenuItem] = relationship()
