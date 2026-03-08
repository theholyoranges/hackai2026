"""Restaurant ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.inventory_item import InventoryItem
    from app.models.menu_item import MenuItem
    from app.models.sales_record import SalesRecord
    from app.models.social_post import SocialPost


class Restaurant(TimestampMixin, Base):
    """A restaurant registered in the system."""

    __tablename__ = "restaurants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cuisine_type: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    owner_name: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    menu_items: Mapped[list[MenuItem]] = relationship(back_populates="restaurant")
    sales_records: Mapped[list[SalesRecord]] = relationship(back_populates="restaurant")
    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates="restaurant")
    social_posts: Mapped[list[SocialPost]] = relationship(back_populates="restaurant")
