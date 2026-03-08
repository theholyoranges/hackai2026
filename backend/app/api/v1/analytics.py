"""Analytics routes for menu, inventory, social, and dashboard summaries."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.engines.inventory_analytics import InventoryAnalyticsEngine
from app.engines.menu_analytics import MenuAnalyticsEngine
from app.engines.social_analytics import SocialAnalyticsEngine
from app.models.recommendation import Recommendation, RecommendationStatus
from app.models.restaurant import Restaurant
from app.models.sales_record import SalesRecord
from app.schemas.analytics import (
    DashboardSummary,
    InventoryAnalytics,
    MenuAnalytics,
    SocialAnalytics,
)

router = APIRouter()


def _require_restaurant(db: Session, restaurant_id: int) -> Restaurant:
    """Return the restaurant or raise 404."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant {restaurant_id} not found",
        )
    return restaurant


# ------------------------------------------------------------------
# Menu analytics
# ------------------------------------------------------------------

@router.get("/menu/{restaurant_id}", response_model=MenuAnalytics)
def get_menu_analytics(restaurant_id: int, db: Session = Depends(get_db)):
    """Full menu analytics for a restaurant."""
    _require_restaurant(db, restaurant_id)
    data = MenuAnalyticsEngine.get_full_analysis(db, restaurant_id)
    # get_demand_trends returns a dict, not a list; flatten to match schema
    demand = data.get("demand_trends", {})
    if isinstance(demand, dict):
        combined = demand.get("by_day_of_week", []) + demand.get("by_hour_of_day", [])
        data["demand_trends"] = combined
    return MenuAnalytics(**data)


# ------------------------------------------------------------------
# Inventory analytics
# ------------------------------------------------------------------

@router.get("/inventory/{restaurant_id}", response_model=InventoryAnalytics)
def get_inventory_analytics(restaurant_id: int, db: Session = Depends(get_db)):
    """Full inventory analytics for a restaurant."""
    _require_restaurant(db, restaurant_id)
    data = InventoryAnalyticsEngine.get_full_analysis(db, restaurant_id)
    return InventoryAnalytics(
        usage_projections=data.get("projected_days_left", []),
        reorder_alerts=data.get("reorder_alerts", []),
        overstock_risks=data.get("overstock_risks", []),
        stockout_risks=data.get("stockout_risks", []),
        expiry_risks=data.get("expiry_risks", []),
        waste_prone=data.get("waste_prone", []),
    )


# ------------------------------------------------------------------
# Social analytics
# ------------------------------------------------------------------

@router.get("/social/{restaurant_id}", response_model=SocialAnalytics)
def get_social_analytics(restaurant_id: int, db: Session = Depends(get_db)):
    """Full social media analytics for a restaurant."""
    _require_restaurant(db, restaurant_id)
    data = SocialAnalyticsEngine.get_full_analysis(db, restaurant_id)
    # best_times is a dict with by_day_of_week and by_hour; flatten for schema
    best_times = data.get("best_times", {})
    if isinstance(best_times, dict):
        best_times_list = best_times.get("by_day_of_week", []) + best_times.get("by_hour", [])
    else:
        best_times_list = best_times
    return SocialAnalytics(
        engagement_by_type=data.get("engagement_by_type", []),
        best_times=best_times_list,
        trending_items=data.get("trending_items", []),
        campaign_opportunities=data.get("campaign_opportunities", []),
    )


# ------------------------------------------------------------------
# Dashboard summary
# ------------------------------------------------------------------

@router.get("/dashboard/{restaurant_id}", response_model=DashboardSummary)
def get_dashboard_summary(restaurant_id: int, db: Session = Depends(get_db)):
    """High-level dashboard combining menu, inventory, and social insights."""
    _require_restaurant(db, restaurant_id)

    # Revenue trend by date
    revenue_rows = (
        db.query(
            sa_func.date(SalesRecord.sale_date).label("date"),
            sa_func.sum(SalesRecord.total_price).label("revenue"),
        )
        .filter(SalesRecord.restaurant_id == restaurant_id)
        .group_by(sa_func.date(SalesRecord.sale_date))
        .order_by(sa_func.date(SalesRecord.sale_date))
        .all()
    )
    revenue_trend = [{"date": str(r.date), "revenue": float(r.revenue)} for r in revenue_rows]

    # Top and bottom items
    top_sellers = MenuAnalyticsEngine.get_top_sellers(db, restaurant_id, limit=1)
    bottom_sellers = MenuAnalyticsEngine.get_bottom_sellers(db, restaurant_id, limit=1)
    top_item = top_sellers[0] if top_sellers else None
    bottom_item = bottom_sellers[0] if bottom_sellers else None

    # High margin opportunities
    margins = MenuAnalyticsEngine.get_margin_analysis(db, restaurant_id)
    high_margin = [m for m in margins if m.get("margin_pct", 0) >= 70]

    # Inventory alerts via engine
    inv_data = InventoryAnalyticsEngine.get_full_analysis(db, restaurant_id)
    waste_alerts = inv_data.get("waste_prone", [])
    stockout_alerts = inv_data.get("stockout_risks", [])

    # Social opportunity via engine
    social_data = SocialAnalyticsEngine.get_full_analysis(db, restaurant_id)
    campaign_ops = social_data.get("campaign_opportunities", [])
    social_opportunity = campaign_ops[0] if campaign_ops else None

    # Top pending recommendations
    recs = (
        db.query(Recommendation)
        .filter(
            Recommendation.restaurant_id == restaurant_id,
            Recommendation.status == RecommendationStatus.pending,
        )
        .limit(3)
        .all()
    )
    top_recommendations = [
        {"id": r.id, "title": r.title, "urgency": r.urgency}
        for r in recs
    ]

    return DashboardSummary(
        revenue_trend=revenue_trend,
        top_item=top_item,
        bottom_item=bottom_item,
        high_margin_opportunities=high_margin,
        waste_alerts=waste_alerts,
        stockout_alerts=stockout_alerts,
        social_opportunity=social_opportunity,
        top_recommendations=top_recommendations,
    )
