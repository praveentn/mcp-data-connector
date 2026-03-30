"""Agent management API routes."""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.agent import AgentCreate, AgentResponse
from backend.agent import sub_agents

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    """List all active agents."""
    agents = await sub_agents.list_agents(db)
    return agents


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new sub-agent."""
    agent = await sub_agents.create_agent(db, data)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific agent by ID."""
    agent = await sub_agents.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: UUID, db: AsyncSession = Depends(get_db)):
    """Deactivate an agent (soft delete)."""
    ok = await sub_agents.deactivate_agent(db, agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent not found")
