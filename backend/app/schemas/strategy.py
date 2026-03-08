"""Pydantic schemas for StrategyDefinition and StrategyHistory."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class StrategyDefinitionResponse(BaseModel):
    """Schema for strategy definition responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: Optional[str]
    description: Optional[str]
    applicability_rules: Optional[dict[str, Any]] = None
    cooldown_days: int
    confidence_threshold: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StrategyHistoryCreate(BaseModel):
    """Schema for creating a new strategy history entry."""

    restaurant_id: int
    strategy_definition_id: int
    menu_item_id: Optional[int] = None
    status: str
    evidence: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None
    expected_impact: Optional[str] = None
    notes: Optional[str] = None


class StrategyHistoryResponse(BaseModel):
    """Schema for strategy history responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    strategy_definition_id: int
    menu_item_id: Optional[int]
    status: str
    evidence: Optional[dict[str, Any]]
    confidence: Optional[float]
    expected_impact: Optional[str]
    actual_impact: Optional[str]
    notes: Optional[str]
    suggested_at: Optional[datetime]
    activated_at: Optional[datetime]
    evaluated_at: Optional[datetime]
    completed_at: Optional[datetime]
    cooldown_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # Enriched fields (optional, populated by API)
    strategy_name: Optional[str] = None
    strategy_category: Optional[str] = None
    menu_item_name: Optional[str] = None


class StrategyStatusUpdate(BaseModel):
    """Schema for updating strategy history status."""

    status: str
    actual_impact: Optional[str] = None
    notes: Optional[str] = None
