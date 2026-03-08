"""Pydantic schemas for Restaurant."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RestaurantCreate(BaseModel):
    """Schema for creating a new restaurant."""

    name: str
    cuisine_type: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    owner_name: Optional[str] = None


class RestaurantResponse(BaseModel):
    """Schema for restaurant responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cuisine_type: Optional[str]
    location: Optional[str]
    description: Optional[str]
    owner_name: Optional[str]
    created_at: datetime
