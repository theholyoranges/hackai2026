"""Pydantic schemas for analytics responses."""

from typing import Any, Optional

from pydantic import BaseModel


class MenuAnalytics(BaseModel):
    """Aggregated menu performance analytics."""

    top_sellers: list[dict[str, Any]]
    bottom_sellers: list[dict[str, Any]]
    revenue_by_item: list[dict[str, Any]]
    margin_analysis: list[dict[str, Any]]
    menu_engineering: list[dict[str, Any]]
    pair_analysis: list[dict[str, Any]]
    category_performance: list[dict[str, Any]]
    demand_trends: list[dict[str, Any]]


class InventoryAnalytics(BaseModel):
    """Aggregated inventory analytics."""

    usage_projections: list[dict[str, Any]]
    reorder_alerts: list[dict[str, Any]]
    overstock_risks: list[dict[str, Any]]
    stockout_risks: list[dict[str, Any]]
    expiry_risks: list[dict[str, Any]]
    waste_prone: list[dict[str, Any]]


class SocialAnalytics(BaseModel):
    """Aggregated social media analytics."""

    engagement_by_type: list[dict[str, Any]]
    engagement_by_platform: list[dict[str, Any]] = []
    best_times: list[dict[str, Any]]
    trending_items: list[dict[str, Any]]
    top_posts: list[dict[str, Any]] = []
    campaign_opportunities: list[dict[str, Any]]


class DashboardSummary(BaseModel):
    """High-level dashboard summary combining all analytics."""

    revenue_trend: list[dict[str, Any]]
    top_item: Optional[dict[str, Any]] = None
    bottom_item: Optional[dict[str, Any]] = None
    high_margin_opportunities: list[dict[str, Any]]
    waste_alerts: list[dict[str, Any]]
    stockout_alerts: list[dict[str, Any]]
    social_opportunity: Optional[dict[str, Any]] = None
    top_recommendations: list[dict[str, Any]]
