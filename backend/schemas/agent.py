"""Pydantic schemas for agents."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    agent_type: str = "sub"
    capabilities: list[str] = []
    config: dict = {}
    parent_agent_id: UUID | None = None


class AgentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    agent_type: str
    capabilities: list[str]
    config: dict
    parent_agent_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
