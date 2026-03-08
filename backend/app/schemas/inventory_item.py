"""Pydantic schemas for InventoryItem."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class InventoryItemCreate(BaseModel):
    """Schema for creating a new inventory item."""

    restaurant_id: int
    ingredient_name: str
    unit: str
    quantity_on_hand: float
    reorder_threshold: Optional[float] = None
    unit_cost: Optional[float] = None
    expiry_date: Optional[date] = None
    supplier: Optional[str] = None


class InventoryItemResponse(BaseModel):
    """Schema for inventory item responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    ingredient_name: str
    unit: str
    quantity_on_hand: float
    reorder_threshold: Optional[float]
    unit_cost: Optional[float]
    expiry_date: Optional[date]
    supplier: Optional[str]
    created_at: datetime
    updated_at: datetime
