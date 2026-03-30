"""Chat API routes."""
import uuid
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc

from backend.database import get_db
from backend.models.message import Message
from backend.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from backend.agent.graph import run_agent
from backend.websocket.broadcaster import TraceBroadcaster

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/send", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a user message and get an agent response."""
    session_id = str(req.session_id or uuid.uuid4())

    # Persist user message
    user_msg = Message(
        session_id=uuid.UUID(session_id),
        role="user",
        content=req.message,
        metadata_={},
    )
    db.add(user_msg)
    await db.flush()

    # Run agent with trace broadcasting
    broadcaster = TraceBroadcaster(session_id=session_id, db=db)

    try:
        response_text = await run_agent(
            session_id=session_id,
            user_message=req.message,
            broadcaster=broadcaster,
        )
    except Exception as exc:
        logger.error("Agent run failed: %s", exc)
        response_text = f"I'm sorry, I encountered an error: {str(exc)}"

    # Persist assistant message
    assistant_msg = Message(
        session_id=uuid.UUID(session_id),
        role="assistant",
        content=response_text,
        metadata_={"session_id": session_id},
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        session_id=uuid.UUID(session_id),
        message=response_text,
        metadata={"session_id": session_id},
    )


@router.get("/history/{session_id}", response_model=list[MessageResponse])
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve chat history for a session."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return []

    result = await db.execute(
        select(Message)
        .where(Message.session_id == sid)
        .order_by(asc(Message.created_at))
    )
    messages = result.scalars().all()
    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            metadata=m.metadata_,
            created_at=m.created_at,
        )
        for m in messages
    ]
