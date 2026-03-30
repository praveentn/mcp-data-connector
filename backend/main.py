"""
MCP Data Connector — FastAPI Backend

Startup:   uvicorn backend.main:app --host 0.0.0.0 --port 7790 --reload
WebSocket: ws://localhost:7790/ws/traces/{session_id}
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import init_db
from backend.api import agents, chat, tools, traces
from backend.websocket.manager import ws_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MCP Data Connector backend on port %d", settings.backend_port)
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="MCP Data Connector API",
    description="Conversational AI orchestration platform with MCP tool integration",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.backend_port - 1}",  # frontend
        "http://localhost:7791",
        "http://localhost:3000",
        "http://127.0.0.1:7791",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(traces.router, prefix="/api")


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws/traces/{session_id}")
async def trace_websocket(websocket: WebSocket, session_id: str):
    """Real-time trace streaming for a session."""
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            # Keep connection alive; client sends pings as text
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, websocket)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "backend_port": settings.backend_port,
        "mcp_server_url": settings.mcp_server_url,
        "active_ws_sessions": len(ws_manager.active_sessions()),
    }


@app.get("/")
async def root():
    return {
        "name": "MCP Data Connector API",
        "docs": "/docs",
        "health": "/health",
    }
