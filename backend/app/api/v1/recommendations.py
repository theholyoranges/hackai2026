"""Recommendation routes for generating and managing AI recommendations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.recommendation import Recommendation, RecommendationStatus
from app.models.restaurant import Restaurant
from app.schemas.recommendation import RecommendationResponse, RecommendationStatusUpdate

router = APIRouter()


def _require_restaurant(db: Session, restaurant_id: int) -> None:
    """Raise 404 if the restaurant does not exist."""
    if not db.query(Restaurant).filter(Restaurant.id == restaurant_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")


@router.post("/generate/{restaurant_id}", response_model=list[RecommendationResponse])
def generate_recommendations(restaurant_id: int, db: Session = Depends(get_db)):
    """Generate new recommendations for a restaurant based on current analytics.

    Delegates to the recommendation engine; returns the newly created recommendations.
    """
    _require_restaurant(db, restaurant_id)

    from app.engines.recommendation_engine import RecommendationEngine

    engine = RecommendationEngine()
    return engine.generate_recommendations(db, restaurant_id)


@router.get("/{restaurant_id}", response_model=list[RecommendationResponse])
def get_recommendations(restaurant_id: int, db: Session = Depends(get_db)):
    """Get current recommendations for a restaurant."""
    _require_restaurant(db, restaurant_id)
    return (
        db.query(Recommendation)
        .filter(Recommendation.restaurant_id == restaurant_id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )


@router.get("/{restaurant_id}/blocked", response_model=list[dict])
def get_blocked_recommendations(restaurant_id: int, db: Session = Depends(get_db)):
    """Get recommendations that are blocked, with reasons."""
    _require_restaurant(db, restaurant_id)
    blocked = (
        db.query(Recommendation)
        .filter(
            Recommendation.restaurant_id == restaurant_id,
            Recommendation.blocked_reason.isnot(None),
        )
        .order_by(Recommendation.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "title": r.title,
            "blocked_reason": r.blocked_reason,
            "strategy_definition_id": r.strategy_definition_id,
        }
        for r in blocked
    ]


@router.put("/{recommendation_id}/status", response_model=RecommendationResponse)
def update_recommendation_status(
    recommendation_id: int,
    payload: RecommendationStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update recommendation status (accept/reject)."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

    try:
        new_status = RecommendationStatus(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{payload.status}'. Valid values: {[s.value for s in RecommendationStatus]}",
        )

    rec.status = new_status

    # If accepted, create a strategy history entry
    if new_status == RecommendationStatus.accepted:
        from app.models.strategy import StrategyHistory, StrategyStatus

        history_entry = StrategyHistory(
            restaurant_id=rec.restaurant_id,
            strategy_definition_id=rec.strategy_definition_id,
            menu_item_id=rec.menu_item_id,
            status=StrategyStatus.accepted,
            evidence=rec.evidence,
            confidence=rec.confidence,
            expected_impact=rec.expected_impact,
            notes=f"Auto-created from recommendation #{rec.id}",
        )
        db.add(history_entry)

    db.commit()
    db.refresh(rec)
    return rec
