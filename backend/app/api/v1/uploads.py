"""CSV upload routes for ingesting restaurant data."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.restaurant import Restaurant
from app.services.csv_parser import (
    parse_inventory_csv,
    parse_menu_csv,
    parse_recipe_mapping_csv,
    parse_sales_csv,
    parse_social_posts_csv,
)
from app.services.pos_converter import convert_pos_csv
from app.services.recipe_generator import generate_recipes_for_menu
from app.services.seed_service import seed_demo_data

router = APIRouter()


class IngestionSummary(BaseModel):
    """Summary returned after CSV ingestion."""

    rows_processed: int
    rows_failed: int
    errors: list[str]


class RecipeGenResponse(BaseModel):
    """Summary returned after recipe generation."""

    recipes_created: int
    menu_items_processed: int
    menu_items_skipped: int
    errors: list[str]


def _validate_restaurant(db: Session, restaurant_id: int) -> None:
    """Raise 404 if the restaurant does not exist."""
    exists = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant {restaurant_id} not found",
        )


@router.post("/menu-items", response_model=IngestionSummary)
async def upload_menu_csv(
    file: UploadFile,
    restaurant_id: int = Query(..., description="Target restaurant ID"),
    db: Session = Depends(get_db),
):
    """Upload a CSV of menu items."""
    _validate_restaurant(db, restaurant_id)
    content = await file.read()
    summary = parse_menu_csv(content, restaurant_id, db)
    return summary


@router.post("/sales-records", response_model=IngestionSummary)
async def upload_sales_csv(
    file: UploadFile,
    restaurant_id: int = Query(..., description="Target restaurant ID"),
    db: Session = Depends(get_db),
):
    """Upload a CSV of sales records."""
    _validate_restaurant(db, restaurant_id)
    content = await file.read()
    summary = parse_sales_csv(content, restaurant_id, db)
    return summary


@router.post("/inventory-items", response_model=IngestionSummary)
async def upload_inventory_csv(
    file: UploadFile,
    restaurant_id: int = Query(..., description="Target restaurant ID"),
    db: Session = Depends(get_db),
):
    """Upload a CSV of inventory items."""
    _validate_restaurant(db, restaurant_id)
    content = await file.read()
    summary = parse_inventory_csv(content, restaurant_id, db)
    return summary


@router.post("/recipe-mappings", response_model=IngestionSummary)
async def upload_recipe_mapping_csv(
    file: UploadFile,
    restaurant_id: int = Query(..., description="Target restaurant ID"),
    db: Session = Depends(get_db),
):
    """Upload a CSV of recipe mappings."""
    _validate_restaurant(db, restaurant_id)
    content = await file.read()
    summary = parse_recipe_mapping_csv(content, restaurant_id, db)
    return summary


@router.post("/social-posts", response_model=IngestionSummary)
async def upload_social_posts_csv(
    file: UploadFile,
    restaurant_id: int = Query(..., description="Target restaurant ID"),
    db: Session = Depends(get_db),
):
    """Upload a CSV of social media posts."""
    _validate_restaurant(db, restaurant_id)
    content = await file.read()
    summary = parse_social_posts_csv(content, restaurant_id, db)
    return summary


@router.post("/pos-sales", response_model=IngestionSummary)
async def upload_pos_sales(
    file: UploadFile,
    restaurant_id: int = Query(..., description="Target restaurant ID"),
    db: Session = Depends(get_db),
):
    """Upload a standard POS-export CSV. Auto-converts columns to our internal format."""
    _validate_restaurant(db, restaurant_id)
    content = await file.read()
    result = convert_pos_csv(content, restaurant_id, db)
    return IngestionSummary(
        rows_processed=result.rows_processed,
        rows_failed=result.rows_failed,
        errors=result.errors,
    )


@router.post("/generate-recipes", response_model=RecipeGenResponse)
def generate_recipes(
    restaurant_id: int = Query(..., description="Target restaurant ID"),
    db: Session = Depends(get_db),
):
    """Generate standard recipe mappings for all menu items."""
    _validate_restaurant(db, restaurant_id)
    result = generate_recipes_for_menu(restaurant_id, db)
    return result


@router.post("/seed-demo")
def seed_demo(db: Session = Depends(get_db)):
    """One-click demo data seeding for both sample restaurants."""
    return seed_demo_data(db)
