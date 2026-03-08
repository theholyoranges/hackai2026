"""Pydantic schemas for SocialPost."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SocialPostCreate(BaseModel):
    """Schema for creating a new social post."""

    restaurant_id: int
    menu_item_id: Optional[int] = None
    platform: str
    post_type: str
    content_summary: Optional[str] = None
    posted_at: datetime
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    reach: Optional[int] = None


class SocialPostResponse(BaseModel):
    """Schema for social post responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    menu_item_id: Optional[int]
    platform: str
    post_type: str
    content_summary: Optional[str]
    posted_at: datetime
    likes: Optional[int]
    comments: Optional[int]
    shares: Optional[int]
    reach: Optional[int]
    created_at: datetime
