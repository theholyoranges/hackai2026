"""Strategy routes for playbook management and strategy history tracking."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Optional

from app.core.database import get_db
from app.models.restaurant import Restaurant
from app.models.strategy import StrategyDefinition, StrategyHistory, StrategyStatus
from app.schemas.strategy import (
    StrategyDefinitionResponse,
    StrategyHistoryResponse,
    StrategyStatusUpdate,
)

router = APIRouter()


class StrategyProgressResponse(BaseModel):
    """Active strategy with progress info for the frontend."""
    id: int
    strategy_name: str
    strategy_category: Optional[str]
    menu_item_name: Optional[str]
    status: str
    expected_impact: Optional[str]
    actual_impact: Optional[str]
    notes: Optional[str]
    activated_at: Optional[datetime]
    days_active: int
    evaluation_ready: bool
    last_verdict: Optional[str] = None
    # Sales tracking
    baseline_daily_orders: Optional[float] = None
    baseline_daily_revenue: Optional[float] = None
    current_daily_orders: Optional[float] = None
    current_daily_revenue: Optional[float] = None
    total_orders_since: Optional[int] = None
    total_revenue_since: Optional[float] = None


class AdoptStrategyRequest(BaseModel):
    """Request to adopt a strategy directly from menu insights."""
    restaurant_id: int
    strategy_code: str
    menu_item_name: Optional[str] = None
    title: str
    evidence: Optional[dict[str, Any]] = None


class AdoptStrategyResponse(BaseModel):
    """Response after adopting a strategy."""
    history_id: int
    strategy_name: str
    status: str
    message: str


class EvaluationResponse(BaseModel):
    """Result of a strategy evaluation."""
    history_id: int
    strategy_name: str
    status: str
    verdict: str
    summary: str
    details: str
    days_active: int
    deltas: dict[str, Any]


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
    from app.models.menu_item import MenuItem

    entries = (
        db.query(StrategyHistory)
        .filter(StrategyHistory.restaurant_id == restaurant_id)
        .order_by(StrategyHistory.created_at.desc())
        .all()
    )

    results = []
    for sh in entries:
        data = StrategyHistoryResponse.model_validate(sh).model_dump()
        sd = db.query(StrategyDefinition).filter(StrategyDefinition.id == sh.strategy_definition_id).first()
        if sd:
            data["strategy_name"] = sd.name
            data["strategy_category"] = sd.category
        if sh.menu_item_id:
            mi = db.query(MenuItem).filter(MenuItem.id == sh.menu_item_id).first()
            if mi:
                data["menu_item_name"] = mi.name
        results.append(data)
    return results


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


@router.get("/history/{restaurant_id}/progress", response_model=list[StrategyProgressResponse])
def get_strategy_progress(restaurant_id: int, db: Session = Depends(get_db)):
    """Get all non-archived strategies with progress info for the tracker UI."""
    _require_restaurant(db, restaurant_id)

    # Include active, accepted, evaluating, successful, failed
    entries = (
        db.query(StrategyHistory)
        .filter(
            StrategyHistory.restaurant_id == restaurant_id,
            StrategyHistory.status != StrategyStatus.archived,
            StrategyHistory.status != StrategyStatus.suggested,
        )
        .order_by(StrategyHistory.created_at.desc())
        .limit(20)
        .all()
    )

    from sqlalchemy import func as sa_func
    from app.models.menu_item import MenuItem
    from app.models.sales_record import SalesRecord

    results = []
    now = datetime.now(timezone.utc)
    for sh in entries:
        sd = db.query(StrategyDefinition).filter(
            StrategyDefinition.id == sh.strategy_definition_id
        ).first()

        menu_item_name = None
        if sh.menu_item_id:
            mi = db.query(MenuItem).filter(MenuItem.id == sh.menu_item_id).first()
            if mi:
                menu_item_name = mi.name

        days_active = 0
        if sh.activated_at:
            activated = sh.activated_at
            if activated.tzinfo is None:
                activated = activated.replace(tzinfo=timezone.utc)
            days_active = (now - activated).days

        # Check last evaluation verdict from evidence
        last_verdict = None
        if sh.evidence and "last_evaluation" in sh.evidence:
            last_verdict = sh.evidence["last_evaluation"].get("ai_verdict", {}).get("verdict")

        # Sales tracking since activation
        baseline_snapshot = (sh.evidence or {}).get("baseline_snapshot", {})
        baseline_daily_orders = baseline_snapshot.get("item_daily_avg_orders")
        baseline_daily_revenue = None
        if baseline_snapshot.get("item_revenue_30d") is not None:
            baseline_daily_revenue = round(
                baseline_snapshot["item_revenue_30d"] / max(baseline_snapshot.get("lookback_days", 30), 1), 2
            )

        current_daily_orders = None
        current_daily_revenue = None
        total_orders_since = None
        total_revenue_since = None

        if sh.activated_at and sh.menu_item_id and days_active > 0:
            cutoff = sh.activated_at.date() if hasattr(sh.activated_at, "date") else sh.activated_at
            row = (
                db.query(
                    sa_func.coalesce(sa_func.sum(SalesRecord.quantity), 0).label("qty"),
                    sa_func.coalesce(sa_func.sum(SalesRecord.total_price), 0).label("rev"),
                )
                .filter(
                    SalesRecord.menu_item_id == sh.menu_item_id,
                    SalesRecord.sale_date >= cutoff,
                )
                .first()
            )
            if row:
                total_orders_since = int(row.qty)
                total_revenue_since = round(float(row.rev), 2)
                current_daily_orders = round(total_orders_since / days_active, 2)
                current_daily_revenue = round(total_revenue_since / days_active, 2)

        results.append(StrategyProgressResponse(
            id=sh.id,
            strategy_name=sd.name if sd else "Unknown",
            strategy_category=sd.category if sd else None,
            menu_item_name=menu_item_name,
            status=sh.status.value if hasattr(sh.status, "value") else str(sh.status),
            expected_impact=sh.expected_impact,
            actual_impact=sh.actual_impact,
            notes=sh.notes,
            activated_at=sh.activated_at,
            days_active=days_active,
            evaluation_ready=days_active >= 3,
            last_verdict=last_verdict,
            baseline_daily_orders=baseline_daily_orders,
            baseline_daily_revenue=baseline_daily_revenue,
            current_daily_orders=current_daily_orders,
            current_daily_revenue=current_daily_revenue,
            total_orders_since=total_orders_since,
            total_revenue_since=total_revenue_since,
        ))

    return results


@router.post("/adopt", response_model=AdoptStrategyResponse)
def adopt_strategy(payload: AdoptStrategyRequest, db: Session = Depends(get_db)):
    """Adopt a strategy directly (e.g. from menu insights recommendations).

    Creates a StrategyHistory entry with status=active and captures a baseline snapshot.
    """
    _require_restaurant(db, payload.restaurant_id)

    # Find the strategy definition by code
    sd = (
        db.query(StrategyDefinition)
        .filter(StrategyDefinition.code == payload.strategy_code, StrategyDefinition.is_active.is_(True))
        .first()
    )
    if not sd:
        # Try fuzzy match by category keyword from the strategy code
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy code '{payload.strategy_code}' not found in playbook",
        )

    # Resolve menu item if provided
    menu_item_id = None
    if payload.menu_item_name:
        from app.models.menu_item import MenuItem
        mi = (
            db.query(MenuItem)
            .filter(
                MenuItem.restaurant_id == payload.restaurant_id,
                MenuItem.name.ilike(payload.menu_item_name),
            )
            .first()
        )
        if mi:
            menu_item_id = mi.id

    # Capture baseline
    from app.engines.strategy_evaluation import capture_baseline_snapshot
    now = datetime.now(timezone.utc)
    baseline = capture_baseline_snapshot(db, payload.restaurant_id, menu_item_id)

    history_entry = StrategyHistory(
        restaurant_id=payload.restaurant_id,
        strategy_definition_id=sd.id,
        menu_item_id=menu_item_id,
        status=StrategyStatus.active,
        evidence={
            **(payload.evidence or {}),
            "baseline_snapshot": baseline,
            "adopted_from": "menu_insights",
            "original_title": payload.title,
        },
        confidence=None,
        expected_impact=None,
        notes=f"Adopted from Menu Insights: {payload.title}",
        suggested_at=now,
        activated_at=now,
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    return AdoptStrategyResponse(
        history_id=history_entry.id,
        strategy_name=sd.name,
        status="active",
        message=f"Strategy '{sd.name}' is now active. We'll track its impact over the coming weeks.",
    )


@router.post("/history/{history_id}/evaluate", response_model=EvaluationResponse)
def evaluate_strategy_endpoint(history_id: int, db: Session = Depends(get_db)):
    """Evaluate the performance of an active strategy using AI.

    Compares baseline metrics (captured at activation) with current metrics
    and asks GPT-4o to produce a verdict.
    """
    from app.engines.strategy_evaluation import evaluate_strategy

    result = evaluate_strategy(db, history_id)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return EvaluationResponse(
        history_id=result["history_id"],
        strategy_name=result["strategy_name"],
        status=result["status"],
        verdict=result["verdict"],
        summary=result["summary"],
        details=result["details"],
        days_active=result["days_active"],
        deltas=result["deltas"],
    )
