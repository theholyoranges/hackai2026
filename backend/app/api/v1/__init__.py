"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.restaurants import router as restaurants_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.strategies import router as strategies_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.chat import router as chat_router

router = APIRouter()

router.include_router(restaurants_router, prefix="/restaurants", tags=["restaurants"])
router.include_router(uploads_router, prefix="/uploads", tags=["uploads"])
router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
router.include_router(strategies_router, prefix="/strategies", tags=["strategies"])
router.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
