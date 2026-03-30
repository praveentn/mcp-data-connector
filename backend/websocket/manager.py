"""WebSocket connection manager — fan-out trace events to browser clients."""
import json
import logging
from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        # session_id (str) → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections.setdefault(session_id, []).append(websocket)
        logger.info("WS connected: session=%s  total=%d", session_id,
                    len(self._connections[session_id]))

    def disconnect(self, session_id: str, websocket: WebSocket):
        conns = self._connections.get(session_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(session_id, None)
        logger.info("WS disconnected: session=%s", session_id)

    async def broadcast(self, session_id: str, payload: dict):
        """Send a JSON message to all WebSocket clients for this session."""
        conns = self._connections.get(session_id, [])
        dead = []
        for ws in conns:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(json.dumps(payload, default=str))
            except Exception as exc:
                logger.warning("WS send failed: %s", exc)
                dead.append(ws)
        for ws in dead:
            self.disconnect(session_id, ws)

    def active_sessions(self) -> list[str]:
        return list(self._connections.keys())


# Singleton
ws_manager = WebSocketManager()
