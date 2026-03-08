"""Strategy History Engine: manages the full lifecycle of strategy instances.

Tracks suggestions, acceptances, activations, evaluations, successes, failures,
and archiving.  Also provides helpers that the recommendation engine uses to
determine which strategies are currently blocked (active, in cooldown, or
recently failed).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.strategy import (
    StrategyDefinition,
    StrategyHistory,
    StrategyStatus,
)


class StrategyHistoryEngine:
    """Stateless service that mutates and queries StrategyHistory rows."""

    # ------------------------------------------------------------------
    # Lifecycle mutations
    # ------------------------------------------------------------------

    @staticmethod
    def record_suggestion(
        db: Session,
        restaurant_id: int,
        strategy_def_id: int,
        menu_item_id: int | None,
        evidence: dict[str, Any],
        confidence: float,
        expected_impact: str,
    ) -> StrategyHistory:
        """Create a new StrategyHistory with status *suggested*."""
        sh = StrategyHistory(
            restaurant_id=restaurant_id,
            strategy_definition_id=strategy_def_id,
            menu_item_id=menu_item_id,
            status=StrategyStatus.suggested,
            evidence=evidence,
            confidence=confidence,
            expected_impact=expected_impact,
            suggested_at=datetime.utcnow(),
        )
        db.add(sh)
        db.commit()
        db.refresh(sh)
        return sh

    @staticmethod
    def accept_strategy(db: Session, history_id: int) -> StrategyHistory:
        """Transition a strategy to *accepted*."""
        sh = db.query(StrategyHistory).filter(StrategyHistory.id == history_id).one()
        sh.status = StrategyStatus.accepted
        db.commit()
        db.refresh(sh)
        return sh

    @staticmethod
    def activate_strategy(db: Session, history_id: int) -> StrategyHistory:
        """Transition a strategy to *active* and record activation timestamp."""
        sh = db.query(StrategyHistory).filter(StrategyHistory.id == history_id).one()
        sh.status = StrategyStatus.active
        sh.activated_at = datetime.utcnow()
        db.commit()
        db.refresh(sh)
        return sh

    @staticmethod
    def start_evaluation(db: Session, history_id: int) -> StrategyHistory:
        """Transition a strategy to *evaluating* and record evaluation timestamp."""
        sh = db.query(StrategyHistory).filter(StrategyHistory.id == history_id).one()
        sh.status = StrategyStatus.evaluating
        sh.evaluated_at = datetime.utcnow()
        db.commit()
        db.refresh(sh)
        return sh

    @staticmethod
    def mark_successful(
        db: Session,
        history_id: int,
        actual_impact: str,
        notes: str | None = None,
    ) -> StrategyHistory:
        """Mark a strategy as *successful*, set cooldown, and record results."""
        sh = db.query(StrategyHistory).filter(StrategyHistory.id == history_id).one()
        sd = (
            db.query(StrategyDefinition)
            .filter(StrategyDefinition.id == sh.strategy_definition_id)
            .one()
        )
        sh.status = StrategyStatus.successful
        sh.actual_impact = actual_impact
        sh.notes = notes
        sh.completed_at = datetime.utcnow()
        sh.cooldown_until = datetime.utcnow() + timedelta(days=sd.cooldown_days)
        db.commit()
        db.refresh(sh)
        return sh

    @staticmethod
    def mark_failed(
        db: Session,
        history_id: int,
        actual_impact: str,
        notes: str | None = None,
    ) -> StrategyHistory:
        """Mark a strategy as *failed*, set cooldown, and record results."""
        sh = db.query(StrategyHistory).filter(StrategyHistory.id == history_id).one()
        sd = (
            db.query(StrategyDefinition)
            .filter(StrategyDefinition.id == sh.strategy_definition_id)
            .one()
        )
        sh.status = StrategyStatus.failed
        sh.actual_impact = actual_impact
        sh.notes = notes
        sh.completed_at = datetime.utcnow()
        sh.cooldown_until = datetime.utcnow() + timedelta(days=sd.cooldown_days)
        db.commit()
        db.refresh(sh)
        return sh

    @staticmethod
    def archive_strategy(db: Session, history_id: int) -> StrategyHistory:
        """Transition a strategy to *archived*."""
        sh = db.query(StrategyHistory).filter(StrategyHistory.id == history_id).one()
        sh.status = StrategyStatus.archived
        db.commit()
        db.refresh(sh)
        return sh

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_active_strategies(db: Session, restaurant_id: int) -> list[StrategyHistory]:
        """Return all strategy histories with status *active* for a restaurant."""
        return (
            db.query(StrategyHistory)
            .filter(
                StrategyHistory.restaurant_id == restaurant_id,
                StrategyHistory.status == StrategyStatus.active,
            )
            .all()
        )

    @staticmethod
    def get_blocked_strategy_codes(db: Session, restaurant_id: int) -> set[str]:
        """Return strategy codes that should NOT be re-suggested.

        A code is blocked if it has any history entry that is:
        - currently *active* or *evaluating*,
        - still within its cooldown window, or
        - *failed* within the last 14 days.
        """
        now = datetime.utcnow()
        fourteen_days_ago = now - timedelta(days=14)

        blocked_rows = (
            db.query(StrategyDefinition.code)
            .join(
                StrategyHistory,
                StrategyHistory.strategy_definition_id == StrategyDefinition.id,
            )
            .filter(
                StrategyHistory.restaurant_id == restaurant_id,
                or_(
                    # Currently active or evaluating
                    StrategyHistory.status.in_([
                        StrategyStatus.active,
                        StrategyStatus.evaluating,
                    ]),
                    # Still in cooldown
                    and_(
                        StrategyHistory.cooldown_until.isnot(None),
                        StrategyHistory.cooldown_until > now,
                    ),
                    # Recently failed (within 14 days)
                    and_(
                        StrategyHistory.status == StrategyStatus.failed,
                        StrategyHistory.completed_at > fourteen_days_ago,
                    ),
                ),
            )
            .distinct()
            .all()
        )

        return {row[0] for row in blocked_rows}

    @staticmethod
    def get_successful_strategies(
        db: Session, restaurant_id: int
    ) -> list[StrategyHistory]:
        """Return all *successful* strategy histories for scale-up consideration."""
        return (
            db.query(StrategyHistory)
            .filter(
                StrategyHistory.restaurant_id == restaurant_id,
                StrategyHistory.status == StrategyStatus.successful,
            )
            .all()
        )

    @staticmethod
    def get_strategy_timeline(
        db: Session, restaurant_id: int, limit: int = 50
    ) -> list[StrategyHistory]:
        """Return the most recent strategy history entries, newest first."""
        return (
            db.query(StrategyHistory)
            .filter(StrategyHistory.restaurant_id == restaurant_id)
            .order_by(StrategyHistory.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def is_strategy_blocked(
        db: Session,
        restaurant_id: int,
        strategy_code: str,
        menu_item_id: int | None = None,
    ) -> bool:
        """Check whether a specific strategy code is blocked for a restaurant.

        When *menu_item_id* is provided the check is scoped to that item;
        otherwise it checks the restaurant as a whole.
        """
        now = datetime.utcnow()
        fourteen_days_ago = now - timedelta(days=14)

        query = (
            db.query(StrategyHistory.id)
            .join(
                StrategyDefinition,
                StrategyHistory.strategy_definition_id == StrategyDefinition.id,
            )
            .filter(
                StrategyHistory.restaurant_id == restaurant_id,
                StrategyDefinition.code == strategy_code,
                or_(
                    StrategyHistory.status.in_([
                        StrategyStatus.active,
                        StrategyStatus.evaluating,
                    ]),
                    and_(
                        StrategyHistory.cooldown_until.isnot(None),
                        StrategyHistory.cooldown_until > now,
                    ),
                    and_(
                        StrategyHistory.status == StrategyStatus.failed,
                        StrategyHistory.completed_at > fourteen_days_ago,
                    ),
                ),
            )
        )

        if menu_item_id is not None:
            query = query.filter(StrategyHistory.menu_item_id == menu_item_id)

        return query.first() is not None
