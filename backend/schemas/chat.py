"""Pydantic schemas for chat."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: UUID | None = None
    message: str


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    session_id: UUID
    message: str
    metadata: dict = {}
