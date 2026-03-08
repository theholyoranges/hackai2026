"""Pydantic schemas for Recommendation."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    """Schema for recommendation responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    strategy_definition_id: int
    menu_item_id: Optional[int]
    title: str
    evidence: Optional[dict[str, Any]]
    urgency: Optional[str]
    blocked_reason: Optional[str]
    explanation_text: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    # Enriched fields
    category: Optional[str] = None
    strategy_name: Optional[str] = None


class RecommendationStatusUpdate(BaseModel):
    """Schema for updating recommendation status."""

    status: str
