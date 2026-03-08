"""RecipeMapping ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem


class RecipeMapping(Base):
    """Maps a menu item to the ingredients (and quantities) required to make it."""

    __tablename__ = "recipe_mappings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    ingredient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_needed: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    menu_item: Mapped[MenuItem] = relationship()
