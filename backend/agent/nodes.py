"""
LangGraph agent nodes.

Each node is an async function that takes AgentState (+ RunnableConfig)
and returns a partial state update dict.  Side effects:
  - Calls Azure OpenAI via LangChain
  - Calls MCP tools via MCPClient
  - Emits trace events via TraceBroadcaster
"""
import json
import time
import logging
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from backend.config import settings
from backend.agent.state import AgentState
from backend.agent.mcp_client import mcp_client

logger = logging.getLogger(__name__)

# ── Shared LLM ────────────────────────────────────────────────────────────────
llm = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    api_key=settings.azure_openai_api_key,
    azure_deployment=settings.azure_deployment,
    api_version=settings.api_version,
    temperature=0.1,
)


def _get_broadcaster(config: RunnableConfig):
    return config.get("configurable", {}).get("broadcaster")


async def _emit(config: RunnableConfig, trace_type: str, payload: dict,
                tool_name: str = None, status: str = "success", duration_ms: int = 0):
    broadcaster = _get_broadcaster(config)
    if broadcaster:
        await broadcaster.emit(
            trace_type=trace_type,
            payload=payload,
            tool_name=tool_name,
            status=status,
            duration_ms=duration_ms,
        )


# ── Node: detect_intent ───────────────────────────────────────────────────────
async def detect_intent(state: AgentState, config: RunnableConfig) -> dict:
    """Classify the user's message into one of the intent categories."""
    start = time.monotonic()

    system = SystemMessage(content=(
        "You are an intent classifier for an AI data platform. "
        "Given a user message, classify it into exactly ONE of these categories:\n"
        "- query_data: User wants to fetch/search data from the CRM or sales database\n"
        "- add_record: User wants to add/create a new customer or record\n"
        "- file_operation: User wants to read or list files\n"
        "- general: General question, greeting, or anything that doesn't need a database/file tool\n\n"
        "Respond with ONLY the category name, nothing else."
    ))
    human = HumanMessage(content=state["user_message"])

    response = await llm.ainvoke([system, human])
    intent = response.content.strip().lower()
    valid = {"query_data", "add_record", "file_operation", "general"}
    if intent not in valid:
        intent = "general"

    duration_ms = int((time.monotonic() - start) * 1000)
    await _emit(config, "intent_detection",
                {"user_message": state["user_message"], "detected_intent": intent},
                duration_ms=duration_ms)

    logger.info("Intent detected: %s", intent)
    return {"intent": intent}


# ── Node: create_plan ─────────────────────────────────────────────────────────
AVAILABLE_TOOLS = """
- query_sales_db(product, min_amount, region, quarter, limit): Query sales records
- get_customers(search, limit): Search/list CRM customers
- add_customer(name, email, company, revenue, region): Create a new customer
- list_files(directory): List files in the data directory
- read_file(filepath): Read file content
"""

async def create_plan(state: AgentState, config: RunnableConfig) -> dict:
    """Create a structured execution plan as a JSON list of tool calls."""
    start = time.monotonic()

    system = SystemMessage(content=(
        "You are a planning agent. Given a user request and intent, "
        "create a JSON execution plan — an ordered list of tool calls to fulfill the request.\n\n"
        f"Available tools:\n{AVAILABLE_TOOLS}\n\n"
        "Return ONLY valid JSON array like:\n"
        '[{"tool": "get_customers", "args": {"search": "alice", "limit": 5}, "reason": "Find customer"}]\n\n'
        "Rules:\n"
        "- Only use tools from the list above\n"
        "- Keep args minimal and relevant\n"
        "- 1-3 steps maximum\n"
        "- Return ONLY the JSON array, no markdown, no explanation"
    ))
    human = HumanMessage(content=(
        f"Intent: {state['intent']}\n"
        f"User request: {state['user_message']}"
    ))

    response = await llm.ainvoke([system, human])
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        plan = json.loads(raw)
        if not isinstance(plan, list):
            plan = [plan]
    except json.JSONDecodeError:
        logger.warning("Plan JSON parse failed, raw=%s", raw)
        plan = []

    duration_ms = int((time.monotonic() - start) * 1000)
    await _emit(config, "plan",
                {"intent": state["intent"], "plan": plan, "raw_response": raw},
                duration_ms=duration_ms)

    logger.info("Plan created: %d steps", len(plan))
    return {"plan": plan}


# ── Node: select_agent ────────────────────────────────────────────────────────
async def select_agent(state: AgentState, config: RunnableConfig) -> dict:
    """Pick the best sub-agent based on the plan's tool requirements."""
    start = time.monotonic()

    plan = state.get("plan") or []
    tools_needed = [step.get("tool", "") for step in plan]

    # Simple rule-based agent selection
    if any(t in ["query_sales_db", "get_customers"] for t in tools_needed):
        agent = "DataQueryAgent"
    elif any(t in ["add_customer"] for t in tools_needed):
        agent = "DataWriteAgent"
    elif any(t in ["list_files", "read_file"] for t in tools_needed):
        agent = "FileAgent"
    else:
        agent = "MainOrchestrator"

    duration_ms = int((time.monotonic() - start) * 1000)
    await _emit(config, "delegation",
                {"tools_needed": tools_needed, "selected_agent": agent},
                duration_ms=duration_ms)

    logger.info("Selected agent: %s", agent)
    return {"selected_agent": agent}


# ── Node: execute_tools ───────────────────────────────────────────────────────
async def execute_tools(state: AgentState, config: RunnableConfig) -> dict:
    """Execute each planned tool call via the MCP client."""
    plan = state.get("plan") or []
    results = []

    for step in plan:
        tool_name = step.get("tool", "")
        args = step.get("args", {})
        reason = step.get("reason", "")

        # Emit tool_call trace
        await _emit(config, "tool_call",
                    {"tool": tool_name, "args": args, "reason": reason},
                    tool_name=tool_name, status="running")

        start = time.monotonic()
        try:
            result_str = await mcp_client.call_tool(tool_name, args)
            duration_ms = int((time.monotonic() - start) * 1000)

            # Parse JSON result if possible
            try:
                result_data = json.loads(result_str)
            except (json.JSONDecodeError, TypeError):
                result_data = result_str

            results.append({
                "tool": tool_name,
                "args": args,
                "result": result_data,
                "status": "success",
            })

            await _emit(config, "tool_result",
                        {"tool": tool_name, "result": result_data},
                        tool_name=tool_name, status="success", duration_ms=duration_ms)

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            error_msg = str(exc)
            logger.error("Tool %s failed: %s", tool_name, error_msg)

            results.append({
                "tool": tool_name,
                "args": args,
                "result": None,
                "error": error_msg,
                "status": "error",
            })

            await _emit(config, "tool_result",
                        {"tool": tool_name, "error": error_msg},
                        tool_name=tool_name, status="error", duration_ms=duration_ms)

    return {"tool_results": results}


# ── Node: compose_response ────────────────────────────────────────────────────
async def compose_response(state: AgentState, config: RunnableConfig) -> dict:
    """Synthesize a natural-language response from tool results."""
    start = time.monotonic()

    tool_results = state.get("tool_results") or []
    intent = state.get("intent", "general")
    user_message = state["user_message"]

    if tool_results:
        results_summary = json.dumps(tool_results, indent=2, default=str)[:4000]
        system = SystemMessage(content=(
            "You are a helpful AI assistant. Given the user's request and the tool results below, "
            "compose a clear, concise, and friendly response. "
            "Format data nicely — use bullet points or tables where appropriate. "
            "Do NOT mention tool names or internal implementation details."
        ))
        human = HumanMessage(content=(
            f"User request: {user_message}\n\n"
            f"Tool results:\n{results_summary}"
        ))
    else:
        # General conversation — no tool results
        system = SystemMessage(content=(
            "You are a helpful AI assistant for an enterprise data platform. "
            "Answer the user's question directly and helpfully."
        ))
        human = HumanMessage(content=user_message)

    response = await llm.ainvoke([system, human])
    final = response.content.strip()

    duration_ms = int((time.monotonic() - start) * 1000)
    await _emit(config, "response",
                {"response_length": len(final), "intent": intent},
                duration_ms=duration_ms)

    logger.info("Response composed (%d chars)", len(final))
    return {"final_response": final}


# ── Conditional routing ───────────────────────────────────────────────────────
def route_after_intent(state: AgentState) -> str:
    """Route to tool planning for structured intents, else skip to response."""
    return "create_plan" if state.get("intent", "general") != "general" else "compose_response"
