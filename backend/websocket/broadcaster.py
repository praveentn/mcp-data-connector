"""
TraceBroadcaster — emits trace events to both the database and WebSocket clients.

Each chat request gets its own broadcaster instance bound to the session_id.
"""
import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.execution_trace import ExecutionTrace
from backend.websocket.manager import ws_manager

logger = logging.getLogger(__name__)


class TraceBroadcaster:
    def __init__(self, session_id: str, db: AsyncSession, agent_id=None):
        self.session_id = session_id
        self.db = db
        self.agent_id = agent_id

    async def emit(
        self,
        trace_type: str,
        payload: dict,
        tool_name: str = None,
        status: str = "success",
        duration_ms: int = 0,
    ):
        """Persist trace to DB and push to all WebSocket clients for the session."""
        trace_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # 1. Persist to DB
        try:
            trace = ExecutionTrace(
                id=trace_id,
                session_id=uuid.UUID(self.session_id),
                agent_id=self.agent_id,
                trace_type=trace_type,
                payload=payload,
                tool_name=tool_name,
                duration_ms=duration_ms,
                status=status,
                created_at=now,
            )
            self.db.add(trace)
            await self.db.flush()  # write without committing the outer transaction
        except Exception as exc:
            logger.warning("Trace DB write failed: %s", exc)

        # 2. Broadcast via WebSocket
        event = {
            "event": "trace",
            "data": {
                "id": str(trace_id),
                "session_id": self.session_id,
                "agent_id": str(self.agent_id) if self.agent_id else None,
                "trace_type": trace_type,
                "payload": payload,
                "tool_name": tool_name,
                "duration_ms": duration_ms,
                "status": status,
                "created_at": now.isoformat(),
            },
        }
        await ws_manager.broadcast(self.session_id, event)
