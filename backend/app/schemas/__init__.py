"""Pydantic schemas for the BistroBrain."""

from app.schemas.analytics import (
    DashboardSummary,
    InventoryAnalytics,
    MenuAnalytics,
    SocialAnalytics,
)
from app.schemas.inventory_item import InventoryItemCreate, InventoryItemResponse
from app.schemas.menu_item import MenuItemCreate, MenuItemResponse
from app.schemas.recipe_mapping import RecipeMappingCreate, RecipeMappingResponse
from app.schemas.recommendation import RecommendationResponse, RecommendationStatusUpdate
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse
from app.schemas.sales_record import SalesRecordCreate, SalesRecordResponse
from app.schemas.social_post import SocialPostCreate, SocialPostResponse
from app.schemas.strategy import (
    StrategyDefinitionResponse,
    StrategyHistoryCreate,
    StrategyHistoryResponse,
    StrategyStatusUpdate,
)

__all__ = [
    # Restaurant
    "RestaurantCreate",
    "RestaurantResponse",
    # MenuItem
    "MenuItemCreate",
    "MenuItemResponse",
    # SalesRecord
    "SalesRecordCreate",
    "SalesRecordResponse",
    # InventoryItem
    "InventoryItemCreate",
    "InventoryItemResponse",
    # RecipeMapping
    "RecipeMappingCreate",
    "RecipeMappingResponse",
    # SocialPost
    "SocialPostCreate",
    "SocialPostResponse",
    # Strategy
    "StrategyDefinitionResponse",
    "StrategyHistoryCreate",
    "StrategyHistoryResponse",
    "StrategyStatusUpdate",
    # Recommendation
    "RecommendationResponse",
    "RecommendationStatusUpdate",
    # Analytics
    "MenuAnalytics",
    "InventoryAnalytics",
    "SocialAnalytics",
    "DashboardSummary",
]
