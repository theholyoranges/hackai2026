"""Strategy evaluation engine.

Captures baseline snapshots when a strategy is activated, computes
post-activation deltas, and uses GPT-4o to produce a human-readable
performance verdict.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.menu_item import MenuItem
from app.models.recipe_mapping import RecipeMapping
from app.models.sales_record import SalesRecord
from app.models.strategy import StrategyDefinition, StrategyHistory, StrategyStatus

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Baseline snapshot
# ------------------------------------------------------------------

def capture_baseline_snapshot(
    db: Session,
    restaurant_id: int,
    menu_item_id: int | None,
    lookback_days: int = 30,
) -> dict[str, Any]:
    """Capture key metrics at the moment a strategy is activated.

    Returns a dict stored in ``StrategyHistory.evidence["baseline_snapshot"]``
    so the evaluation engine can compute deltas later.
    """
    cutoff = date.today() - timedelta(days=lookback_days)

    snapshot: dict[str, Any] = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": lookback_days,
    }

    # Restaurant-wide revenue
    total_rev = (
        db.query(func.coalesce(func.sum(SalesRecord.total_price), 0))
        .filter(
            SalesRecord.restaurant_id == restaurant_id,
            SalesRecord.sale_date >= cutoff,
        )
        .scalar()
    )
    total_qty = (
        db.query(func.coalesce(func.sum(SalesRecord.quantity), 0))
        .filter(
            SalesRecord.restaurant_id == restaurant_id,
            SalesRecord.sale_date >= cutoff,
        )
        .scalar()
    )
    snapshot["total_revenue_30d"] = float(total_rev)
    snapshot["total_orders_30d"] = int(total_qty)

    # Item-specific metrics if a menu item is targeted
    if menu_item_id:
        item = db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
        if item:
            item_rev = (
                db.query(func.coalesce(func.sum(SalesRecord.total_price), 0))
                .filter(
                    SalesRecord.menu_item_id == menu_item_id,
                    SalesRecord.sale_date >= cutoff,
                )
                .scalar()
            )
            item_qty = (
                db.query(func.coalesce(func.sum(SalesRecord.quantity), 0))
                .filter(
                    SalesRecord.menu_item_id == menu_item_id,
                    SalesRecord.sale_date >= cutoff,
                )
                .scalar()
            )
            snapshot["item_name"] = item.name
            snapshot["item_price"] = float(item.price)
            snapshot["item_revenue_30d"] = float(item_rev)
            snapshot["item_orders_30d"] = int(item_qty)
            snapshot["item_daily_avg_orders"] = round(int(item_qty) / max(lookback_days, 1), 2)

    return snapshot


# ------------------------------------------------------------------
# Post-activation metrics
# ------------------------------------------------------------------

def capture_current_metrics(
    db: Session,
    restaurant_id: int,
    menu_item_id: int | None,
    since: datetime,
) -> dict[str, Any]:
    """Capture metrics from ``since`` to now for comparison with baseline."""
    # Ensure timezone-aware comparison
    since_aware = since.replace(tzinfo=timezone.utc) if since.tzinfo is None else since
    days_active = max((datetime.now(timezone.utc) - since_aware).days, 1)
    cutoff = since.date() if hasattr(since, "date") else since

    metrics: dict[str, Any] = {
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "days_active": days_active,
    }

    total_rev = (
        db.query(func.coalesce(func.sum(SalesRecord.total_price), 0))
        .filter(
            SalesRecord.restaurant_id == restaurant_id,
            SalesRecord.sale_date >= cutoff,
        )
        .scalar()
    )
    total_qty = (
        db.query(func.coalesce(func.sum(SalesRecord.quantity), 0))
        .filter(
            SalesRecord.restaurant_id == restaurant_id,
            SalesRecord.sale_date >= cutoff,
        )
        .scalar()
    )
    metrics["total_revenue_since"] = float(total_rev)
    metrics["total_orders_since"] = int(total_qty)
    metrics["daily_avg_revenue"] = round(float(total_rev) / days_active, 2)

    if menu_item_id:
        item = db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
        if item:
            item_rev = (
                db.query(func.coalesce(func.sum(SalesRecord.total_price), 0))
                .filter(
                    SalesRecord.menu_item_id == menu_item_id,
                    SalesRecord.sale_date >= cutoff,
                )
                .scalar()
            )
            item_qty = (
                db.query(func.coalesce(func.sum(SalesRecord.quantity), 0))
                .filter(
                    SalesRecord.menu_item_id == menu_item_id,
                    SalesRecord.sale_date >= cutoff,
                )
                .scalar()
            )
            metrics["item_name"] = item.name
            metrics["item_revenue_since"] = float(item_rev)
            metrics["item_orders_since"] = int(item_qty)
            metrics["item_daily_avg_orders"] = round(int(item_qty) / days_active, 2)

    return metrics


# ------------------------------------------------------------------
# Compute deltas
# ------------------------------------------------------------------

def compute_deltas(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Compare baseline vs current and compute percentage changes."""
    deltas: dict[str, Any] = {}

    # Restaurant-wide
    base_rev_daily = baseline.get("total_revenue_30d", 0) / max(baseline.get("lookback_days", 30), 1)
    curr_rev_daily = current.get("daily_avg_revenue", 0)
    if base_rev_daily > 0:
        deltas["daily_revenue_change_pct"] = round(
            (curr_rev_daily - base_rev_daily) / base_rev_daily * 100, 1
        )

    # Item-specific
    base_item_daily = baseline.get("item_daily_avg_orders", 0)
    curr_item_daily = current.get("item_daily_avg_orders", 0)
    if base_item_daily > 0:
        deltas["item_daily_orders_change_pct"] = round(
            (curr_item_daily - base_item_daily) / base_item_daily * 100, 1
        )

    base_item_rev = baseline.get("item_revenue_30d", 0) / max(baseline.get("lookback_days", 30), 1)
    curr_item_rev = current.get("item_revenue_since", 0) / max(current.get("days_active", 1), 1)
    if base_item_rev > 0:
        deltas["item_daily_revenue_change_pct"] = round(
            (curr_item_rev - base_item_rev) / base_item_rev * 100, 1
        )

    deltas["days_active"] = current.get("days_active", 0)

    return deltas


# ------------------------------------------------------------------
# GPT-4o evaluation
# ------------------------------------------------------------------

def evaluate_strategy_with_ai(
    strategy_name: str,
    expected_impact: str | None,
    baseline: dict[str, Any],
    current: dict[str, Any],
    deltas: dict[str, Any],
) -> dict[str, Any]:
    """Call GPT-4o to produce a human-readable verdict on strategy performance.

    Returns {"verdict": "successful"|"too_early"|"failed", "summary": "...",
             "details": "..."}.
    """
    try:
        from openai import OpenAI
        from app.core.config import settings
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception as e:
        logger.error("Failed to create OpenAI client: %s", e)
        return {
            "verdict": "too_early",
            "summary": "Could not connect to AI service for evaluation.",
            "details": "",
        }

    system_prompt = """You are a restaurant business analyst evaluating whether a strategy the owner adopted is working.

You will receive:
- The strategy name and expected impact
- Baseline metrics (before the strategy was activated)
- Current metrics (since activation)
- Computed percentage changes

Your job:
1. Determine if the strategy is **successful**, **too early to tell** (< 7 days of data), or **not working**
2. Write a brief, encouraging summary (2-3 sentences) in plain language
3. Write a longer details section (3-5 sentences) with specific numbers

Respond ONLY with valid JSON:
{
  "verdict": "successful" | "too_early" | "failed",
  "summary": "...",
  "details": "..."
}

Use plain language. No jargon. Be honest but constructive — if it failed, suggest why and what to try next."""

    user_prompt = f"""Strategy: {strategy_name}
Expected impact: {expected_impact or "Not specified"}

Baseline (30 days before activation):
{json.dumps(baseline, indent=2, default=str)}

Current (since activation):
{json.dumps(current, indent=2, default=str)}

Changes:
{json.dumps(deltas, indent=2, default=str)}

Evaluate this strategy's performance."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=512,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        return json.loads(content)
    except Exception as e:
        logger.error("GPT-4o evaluation failed: %s", e)
        return {
            "verdict": "too_early",
            "summary": "AI evaluation temporarily unavailable.",
            "details": str(e),
        }


# ------------------------------------------------------------------
# Full evaluation pipeline
# ------------------------------------------------------------------

def evaluate_strategy(
    db: Session,
    history_id: int,
) -> dict[str, Any]:
    """Run the full evaluation pipeline for a strategy history entry.

    Returns the evaluation result and updates the StrategyHistory record.
    """
    sh = db.query(StrategyHistory).filter(StrategyHistory.id == history_id).first()
    if not sh:
        return {"error": "Strategy history entry not found"}

    sd = db.query(StrategyDefinition).filter(
        StrategyDefinition.id == sh.strategy_definition_id
    ).first()

    if not sh.activated_at:
        return {"error": "Strategy was never activated"}

    # Get baseline from stored evidence
    baseline = (sh.evidence or {}).get("baseline_snapshot", {})
    if not baseline:
        # Recapture baseline from 30 days before activation
        baseline = capture_baseline_snapshot(
            db, sh.restaurant_id, sh.menu_item_id, lookback_days=30
        )

    # Capture current metrics since activation
    current = capture_current_metrics(
        db, sh.restaurant_id, sh.menu_item_id, sh.activated_at
    )

    # Compute deltas
    deltas = compute_deltas(baseline, current)

    # AI evaluation
    ai_result = evaluate_strategy_with_ai(
        strategy_name=sd.name if sd else "Unknown strategy",
        expected_impact=sh.expected_impact,
        baseline=baseline,
        current=current,
        deltas=deltas,
    )

    # Update strategy history based on verdict
    verdict = ai_result.get("verdict", "too_early")
    sh.evaluated_at = datetime.now(timezone.utc)

    if verdict == "successful":
        sh.status = StrategyStatus.successful
        sh.completed_at = datetime.now(timezone.utc)
        if sd:
            sh.cooldown_until = datetime.now(timezone.utc) + timedelta(days=sd.cooldown_days)
    elif verdict == "failed":
        sh.status = StrategyStatus.failed
        sh.completed_at = datetime.now(timezone.utc)
        if sd:
            sh.cooldown_until = datetime.now(timezone.utc) + timedelta(days=sd.cooldown_days)
    else:
        sh.status = StrategyStatus.evaluating

    sh.actual_impact = ai_result.get("summary", "")
    sh.notes = ai_result.get("details", "")

    # Store evaluation data in evidence
    evidence = sh.evidence or {}
    evidence["last_evaluation"] = {
        "current_metrics": current,
        "deltas": deltas,
        "ai_verdict": ai_result,
    }
    sh.evidence = evidence

    db.commit()
    db.refresh(sh)

    return {
        "history_id": sh.id,
        "strategy_name": sd.name if sd else "Unknown",
        "status": sh.status.value if hasattr(sh.status, "value") else str(sh.status),
        "verdict": verdict,
        "summary": ai_result.get("summary", ""),
        "details": ai_result.get("details", ""),
        "baseline": baseline,
        "current": current,
        "deltas": deltas,
        "days_active": deltas.get("days_active", 0),
    }
