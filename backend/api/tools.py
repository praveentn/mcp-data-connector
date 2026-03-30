"""Tools registry API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.tool import Tool
from backend.agent.mcp_client import mcp_client

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
async def list_tools(db: AsyncSession = Depends(get_db)):
    """List all registered tools from the database."""
    result = await db.execute(
        select(Tool).where(Tool.is_active == True).order_by(Tool.name)
    )
    tools = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "permission_level": t.permission_level,
        }
        for t in tools
    ]


@router.get("/mcp/discover")
async def discover_mcp_tools():
    """Discover tools directly from the live MCP server."""
    try:
        tools = await mcp_client.list_tools()
        return {"source": "mcp_server", "tools": tools}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MCP server unavailable: {exc}")


@router.get("/{tool_name}")
async def get_tool(tool_name: str, db: AsyncSession = Depends(get_db)):
    """Get a specific tool's schema by name."""
    result = await db.execute(select(Tool).where(Tool.name == tool_name))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {
        "id": str(tool.id),
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema,
        "permission_level": tool.permission_level,
    }
