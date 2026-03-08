"""Strategy routes for playbook management and strategy history tracking."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.restaurant import Restaurant
from app.models.strategy import StrategyDefinition, StrategyHistory, StrategyStatus
from app.schemas.strategy import (
    StrategyDefinitionResponse,
    StrategyHistoryResponse,
    StrategyStatusUpdate,
)

router = APIRouter()


def _require_restaurant(db: Session, restaurant_id: int) -> None:
    """Raise 404 if the restaurant does not exist."""
    if not db.query(Restaurant).filter(Restaurant.id == restaurant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")


# ------------------------------------------------------------------
# Playbook
# ------------------------------------------------------------------

@router.get("/playbook", response_model=list[StrategyDefinitionResponse])
def list_strategy_definitions(db: Session = Depends(get_db)):
    """Return all strategy definitions (the playbook)."""
    return (
        db.query(StrategyDefinition)
        .filter(StrategyDefinition.is_active.is_(True))
        .order_by(StrategyDefinition.category, StrategyDefinition.name)
        .all()
    )


# ------------------------------------------------------------------
# History
# ------------------------------------------------------------------

@router.get("/history/{restaurant_id}", response_model=list[StrategyHistoryResponse])
def get_strategy_history(restaurant_id: int, db: Session = Depends(get_db)):
    """Get the full strategy history timeline for a restaurant."""
    _require_restaurant(db, restaurant_id)
    return (
        db.query(StrategyHistory)
        .filter(StrategyHistory.restaurant_id == restaurant_id)
        .order_by(StrategyHistory.created_at.desc())
        .all()
    )


@router.put("/history/{history_id}/status", response_model=StrategyHistoryResponse)
def update_strategy_status(
    history_id: int,
    payload: StrategyStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update the status of a strategy history entry."""
    entry = db.query(StrategyHistory).filter(StrategyHistory.id == history_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy history entry not found")

    try:
        new_status = StrategyStatus(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{payload.status}'. Valid values: {[s.value for s in StrategyStatus]}",
        )

    entry.status = new_status
    if payload.actual_impact is not None:
        entry.actual_impact = payload.actual_impact
    if payload.notes is not None:
        entry.notes = payload.notes

    # Track lifecycle timestamps
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    if new_status == StrategyStatus.active and entry.activated_at is None:
        entry.activated_at = now
    elif new_status == StrategyStatus.evaluating and entry.evaluated_at is None:
        entry.evaluated_at = now
    elif new_status in (StrategyStatus.successful, StrategyStatus.failed, StrategyStatus.archived):
        if entry.completed_at is None:
            entry.completed_at = now

    db.commit()
    db.refresh(entry)
    return entry


@router.get("/history/{restaurant_id}/active", response_model=list[StrategyHistoryResponse])
def get_active_strategies(restaurant_id: int, db: Session = Depends(get_db)):
    """Get currently active strategies for a restaurant."""
    _require_restaurant(db, restaurant_id)
    active_statuses = [StrategyStatus.accepted, StrategyStatus.active, StrategyStatus.evaluating]
    return (
        db.query(StrategyHistory)
        .filter(
            StrategyHistory.restaurant_id == restaurant_id,
            StrategyHistory.status.in_(active_statuses),
        )
        .order_by(StrategyHistory.created_at.desc())
        .all()
    )


@router.get("/history/{restaurant_id}/blocked", response_model=list[str])
def get_blocked_strategy_codes(restaurant_id: int, db: Session = Depends(get_db)):
    """Return strategy codes that are currently blocked (active or in cooldown)."""
    _require_restaurant(db, restaurant_id)

    from app.engines.strategy_history_engine import StrategyHistoryEngine

    blocked_codes = StrategyHistoryEngine.get_blocked_strategy_codes(db, restaurant_id)
    return sorted(blocked_codes)
