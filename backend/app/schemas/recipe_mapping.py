"""Pydantic schemas for RecipeMapping."""

from pydantic import BaseModel, ConfigDict


class RecipeMappingCreate(BaseModel):
    """Schema for creating a new recipe mapping."""

    menu_item_id: int
    ingredient_name: str
    quantity_needed: float
    unit: str


class RecipeMappingResponse(BaseModel):
    """Schema for recipe mapping responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    menu_item_id: int
    ingredient_name: str
    quantity_needed: float
    unit: str
