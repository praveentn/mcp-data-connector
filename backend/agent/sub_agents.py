"""Sub-agent registry — load and manage dynamic sub-agents from the database."""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.agent import Agent
from backend.schemas.agent import AgentCreate, AgentResponse

logger = logging.getLogger(__name__)


async def list_agents(db: AsyncSession) -> list[Agent]:
    """Fetch all active agents from the database."""
    result = await db.execute(
        select(Agent).where(Agent.is_active == True).order_by(Agent.created_at)
    )
    return list(result.scalars().all())


async def get_agent_by_id(db: AsyncSession, agent_id) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    return result.scalar_one_or_none()


async def create_agent(db: AsyncSession, data: AgentCreate) -> Agent:
    """Persist a new agent and return the created record."""
    agent = Agent(
        name=data.name,
        description=data.description,
        agent_type=data.agent_type,
        capabilities=data.capabilities,
        config=data.config,
        parent_agent_id=data.parent_agent_id,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    logger.info("Created agent: %s (%s)", agent.name, agent.id)
    return agent


async def deactivate_agent(db: AsyncSession, agent_id) -> bool:
    """Soft-delete an agent by setting is_active = False."""
    agent = await get_agent_by_id(db, agent_id)
    if not agent:
        return False
    agent.is_active = False
    await db.commit()
    return True
