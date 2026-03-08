"""Strategy-related ORM models: StrategyDefinition and StrategyHistory."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, ForeignKey, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem
    from app.models.restaurant import Restaurant


class StrategyStatus(str, enum.Enum):
    """Lifecycle status of a strategy instance."""

    suggested = "suggested"
    accepted = "accepted"
    active = "active"
    evaluating = "evaluating"
    successful = "successful"
    failed = "failed"
    archived = "archived"


class StrategyDefinition(TimestampMixin, Base):
    """A reusable strategy template that the copilot can recommend."""

    __tablename__ = "strategy_definitions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    applicability_rules: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    blocked_conditions: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    expected_evidence_fields: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    cooldown_days: Mapped[int] = mapped_column(default=14)
    confidence_threshold: Mapped[float] = mapped_column(Numeric(3, 2), default=0.5)
    expected_kpi_targets: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    history_entries: Mapped[list[StrategyHistory]] = relationship(back_populates="strategy_definition")


class StrategyHistory(TimestampMixin, Base):
    """An instance of a strategy being applied to a specific restaurant."""

    __tablename__ = "strategy_history"

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    strategy_definition_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_definitions.id"), nullable=False
    )
    menu_item_id: Mapped[int | None] = mapped_column(ForeignKey("menu_items.id"))
    status: Mapped[StrategyStatus] = mapped_column(
        Enum(StrategyStatus), default=StrategyStatus.suggested
    )
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    expected_impact: Mapped[str | None] = mapped_column(Text)
    actual_impact: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    suggested_at: Mapped[datetime | None] = mapped_column()
    activated_at: Mapped[datetime | None] = mapped_column()
    evaluated_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    cooldown_until: Mapped[datetime | None] = mapped_column()

    # Relationships
    restaurant: Mapped[Restaurant] = relationship()
    strategy_definition: Mapped[StrategyDefinition] = relationship(back_populates="history_entries")
    menu_item: Mapped[MenuItem | None] = relationship()
