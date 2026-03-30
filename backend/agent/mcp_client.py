"""
MCP Client — connects to the FastMCP server and invokes tools.

FastMCP 3.x returns CallToolResult objects; this wrapper normalises the
response to a plain string so the rest of the agent code stays simple.
"""
import json
import logging
from backend.config import settings

logger = logging.getLogger(__name__)


def _extract_text(result) -> str:
    """
    Normalise a FastMCP / MCP SDK call_tool response to a string.

    FastMCP 3.x call_tool() returns a CallToolResult with a .content list,
    where each item is a TextContent / ImageContent / EmbeddedResource.
    Older versions returned the list directly.
    """
    # CallToolResult object (FastMCP 3.x)
    if hasattr(result, "content"):
        parts = result.content
    elif isinstance(result, list):
        parts = result
    else:
        return str(result)

    texts = []
    for item in parts:
        if hasattr(item, "text"):
            texts.append(item.text)
        else:
            texts.append(str(item))

    return "\n".join(texts) if texts else "[]"


class MCPClient:
    def __init__(self, url: str = None):
        self.url = url or settings.mcp_server_url

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a tool on the MCP server and return the result as a string."""
        try:
            from fastmcp import Client

            async with Client(self.url) as client:
                result = await client.call_tool(tool_name, arguments)
                return _extract_text(result)
        except Exception as exc:
            logger.error("MCPClient.call_tool(%s) failed: %s", tool_name, exc)
            raise

    async def list_tools(self) -> list[dict]:
        """Retrieve the list of tools registered on the MCP server."""
        try:
            from fastmcp import Client

            async with Client(self.url) as client:
                raw = await client.list_tools()
                # FastMCP 3.x may return a ListToolsResult or a plain list
                tools = raw.tools if hasattr(raw, "tools") else raw
                return [
                    {
                        "name": t.name,
                        "description": t.description or "",
                        "input_schema": (
                            t.inputSchema if hasattr(t, "inputSchema") else
                            t.input_schema if hasattr(t, "input_schema") else {}
                        ),
                    }
                    for t in tools
                ]
        except Exception as exc:
            logger.warning("MCPClient.list_tools() failed: %s", exc)
            return []


# Singleton client shared across requests
mcp_client = MCPClient()
