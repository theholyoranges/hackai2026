"""Pydantic schemas for SalesRecord."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SalesRecordCreate(BaseModel):
    """Schema for creating a new sales record."""

    restaurant_id: int
    menu_item_id: int
    quantity: int
    total_price: float
    order_id: str
    sale_date: datetime
    day_of_week: Optional[str] = None
    hour_of_day: Optional[int] = None


class SalesRecordResponse(BaseModel):
    """Schema for sales record responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    menu_item_id: int
    quantity: int
    total_price: float
    order_id: Optional[str]
    sale_date: datetime
    day_of_week: Optional[str]
    hour_of_day: Optional[int]
    created_at: datetime
