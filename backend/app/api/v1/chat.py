"""Chat route for AI-powered restaurant copilot conversations."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.restaurant import Restaurant
from app.services.chat_service import process_chat

router = APIRouter()


class ChatRequest(BaseModel):
    """Incoming chat message."""

    restaurant_id: int
    message: str


class ChatResponse(BaseModel):
    """AI-generated chat response."""

    response: str
    restaurant_id: int


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Accept a chat message and return an AI response grounded in analytics and strategy history."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == payload.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    response_text = process_chat(db, payload.restaurant_id, payload.message)
    return ChatResponse(response=response_text, restaurant_id=payload.restaurant_id)
