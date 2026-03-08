"""Recommendation routes for generating and managing AI recommendations."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.recommendation import Recommendation, RecommendationStatus
from app.models.restaurant import Restaurant
from app.schemas.recommendation import RecommendationResponse, RecommendationStatusUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


class ElaborateRequest(BaseModel):
    """Request body for AI elaboration."""
    title: str
    description: str
    target_item: str | None = None
    context: dict | None = None


class ElaborateResponse(BaseModel):
    """Response from AI elaboration."""
    elaboration: str


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
    """Get current recommendations for a restaurant, enriched with strategy category."""
    _require_restaurant(db, restaurant_id)
    from app.models.strategy import StrategyDefinition

    recs = (
        db.query(Recommendation)
        .filter(Recommendation.restaurant_id == restaurant_id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )

    results = []
    for rec in recs:
        data = RecommendationResponse.model_validate(rec).model_dump()
        sd = db.query(StrategyDefinition).filter(
            StrategyDefinition.id == rec.strategy_definition_id
        ).first()
        if sd:
            data["category"] = sd.category
            data["strategy_name"] = sd.name
        results.append(data)
    return results


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

    # If accepted, create a strategy history entry and immediately activate it
    if new_status == RecommendationStatus.accepted:
        from datetime import datetime, timezone
        from app.models.strategy import StrategyHistory, StrategyStatus
        from app.engines.strategy_evaluation import capture_baseline_snapshot

        now = datetime.now(timezone.utc)

        # Capture baseline metrics at the moment of activation
        baseline = capture_baseline_snapshot(db, rec.restaurant_id, rec.menu_item_id)

        history_entry = StrategyHistory(
            restaurant_id=rec.restaurant_id,
            strategy_definition_id=rec.strategy_definition_id,
            menu_item_id=rec.menu_item_id,
            status=StrategyStatus.active,
            evidence={
                **(rec.evidence or {}),
                "baseline_snapshot": baseline,
            },
            notes=f"Adopted from Recommendations",
            suggested_at=now,
            activated_at=now,
        )
        db.add(history_entry)

    db.commit()
    db.refresh(rec)
    return rec


@router.post("/elaborate", response_model=ElaborateResponse)
def elaborate_recommendation(payload: ElaborateRequest):
    """Call GPT-4o to elaborate on a recommendation with actionable detail.

    Takes a short recommendation title + description and returns a detailed,
    restaurant-owner-friendly action plan with examples.
    """
    try:
        from openai import OpenAI
        from app.core.config import settings

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception as e:
        logger.error("Failed to create OpenAI client: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable",
        )

    system_prompt = """You are a friendly, experienced restaurant growth consultant.
A restaurant owner has received a short AI recommendation and wants to understand it better.

Your job is to elaborate on the recommendation in a way that is:
- Written in plain, non-technical language a restaurant owner can understand
- Actionable with specific step-by-step instructions
- Includes real-world examples relevant to their restaurant
- Mentions expected outcomes and timeframes
- Practical and immediately implementable
- Encouraging and supportive in tone

Format your response in clean paragraphs. Use bullet points for action steps.
Keep it under 300 words. Do NOT use markdown headers (#).
Start directly with the explanation — no preamble like "Great question" or "Sure!"."""

    context_text = ""
    if payload.context:
        context_text = f"\n\nAdditional context:\n{json.dumps(payload.context, indent=2, default=str)}"

    user_prompt = f"""Recommendation: {payload.title}
Summary: {payload.description}
{f'Target item: {payload.target_item}' if payload.target_item else ''}
{context_text}

Please elaborate on this recommendation with specific, actionable advice for the restaurant owner."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=1024,
        )
        elaboration = response.choices[0].message.content.strip()
        return ElaborateResponse(elaboration=elaboration)
    except Exception as e:
        logger.error("GPT-4o elaboration failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate elaboration",
        )
