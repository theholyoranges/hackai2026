"""Recommendation ORM model."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem
    from app.models.restaurant import Restaurant
    from app.models.strategy import StrategyDefinition


class RecommendationStatus(str, enum.Enum):
    """Status of a recommendation."""

    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    implemented = "implemented"


class Recommendation(TimestampMixin, Base):
    """An AI-generated recommendation for a restaurant."""

    __tablename__ = "recommendations"

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    strategy_definition_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_definitions.id"), nullable=False
    )
    menu_item_id: Mapped[int | None] = mapped_column(ForeignKey("menu_items.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    urgency: Mapped[str | None] = mapped_column(String(50))
    expected_impact: Mapped[str | None] = mapped_column(Text)
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    explanation_input: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    explanation_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus), default=RecommendationStatus.pending
    )

    # Relationships
    restaurant: Mapped[Restaurant] = relationship()
    strategy_definition: Mapped[StrategyDefinition] = relationship()
    menu_item: Mapped[MenuItem | None] = relationship()
