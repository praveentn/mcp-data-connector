"""LangGraph agent state definition."""
from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    session_id: str
    user_message: str
    intent: str | None                     # detected intent category
    plan: list[dict] | None                # list of {tool, args, reason} steps
    selected_agent: str | None             # which sub-agent handles this
    tool_results: Annotated[list[dict], operator.add]  # accumulated tool outputs
    final_response: str | None
    error: str | None
