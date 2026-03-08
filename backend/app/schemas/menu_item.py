"""Pydantic schemas for MenuItem."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MenuItemCreate(BaseModel):
    """Schema for creating a new menu item."""

    restaurant_id: int
    name: str
    category: str
    price: float
    ingredient_cost: Optional[float] = None
    description: Optional[str] = None
    is_active: bool = True


class MenuItemResponse(BaseModel):
    """Schema for menu item responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    category: Optional[str]
    price: float
    ingredient_cost: Optional[float]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
