"""Pydantic schemas for execution traces."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class TraceEvent(BaseModel):
    id: UUID
    session_id: UUID
    agent_id: UUID | None
    trace_type: str
    payload: dict
    tool_name: str | None
    duration_ms: int | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TraceStreamMessage(BaseModel):
    event: str = "trace"
    data: dict
