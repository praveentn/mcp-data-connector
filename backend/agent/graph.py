"""
LangGraph agent graph definition.

Flow:
  START → detect_intent → [conditional] → create_plan → select_agent → execute_tools → compose_response → END
                                        ↘ (general intent) ────────────────────────────────────→ compose_response
"""
from langgraph.graph import StateGraph, START, END

from backend.agent.state import AgentState
from backend.agent.nodes import (
    detect_intent,
    create_plan,
    select_agent,
    execute_tools,
    compose_response,
    route_after_intent,
)


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("create_plan", create_plan)
    workflow.add_node("select_agent", select_agent)
    workflow.add_node("execute_tools", execute_tools)
    workflow.add_node("compose_response", compose_response)

    # Edges
    workflow.add_edge(START, "detect_intent")
    workflow.add_conditional_edges(
        "detect_intent",
        route_after_intent,
        {
            "create_plan": "create_plan",
            "compose_response": "compose_response",
        },
    )
    workflow.add_edge("create_plan", "select_agent")
    workflow.add_edge("select_agent", "execute_tools")
    workflow.add_edge("execute_tools", "compose_response")
    workflow.add_edge("compose_response", END)

    return workflow


# Compiled graph — shared across requests
graph = build_graph().compile()


async def run_agent(session_id: str, user_message: str, broadcaster=None) -> str:
    """
    Run the agent graph for a given user message.

    Args:
        session_id: Unique session identifier
        user_message: The user's input text
        broadcaster: Optional TraceBroadcaster for real-time trace streaming

    Returns:
        The agent's final response text
    """
    initial_state: AgentState = {
        "session_id": session_id,
        "user_message": user_message,
        "intent": None,
        "plan": None,
        "selected_agent": None,
        "tool_results": [],
        "final_response": None,
        "error": None,
    }

    config = {
        "configurable": {
            "session_id": session_id,
            "broadcaster": broadcaster,
        }
    }

    result = await graph.ainvoke(initial_state, config=config)
    return result.get("final_response") or "I encountered an error processing your request."
