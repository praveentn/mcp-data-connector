"""Execution trace API routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc

from backend.database import get_db
from backend.models.execution_trace import ExecutionTrace
from backend.schemas.trace import TraceEvent

router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("/{session_id}", response_model=list[TraceEvent])
async def get_traces(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all execution traces for a session."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    result = await db.execute(
        select(ExecutionTrace)
        .where(ExecutionTrace.session_id == sid)
        .order_by(asc(ExecutionTrace.created_at))
    )
    return list(result.scalars().all())


@router.get("/{session_id}/summary")
async def get_traces_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    """Aggregate trace stats for a session."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    result = await db.execute(
        select(
            ExecutionTrace.trace_type,
            func.count(ExecutionTrace.id).label("count"),
            func.sum(ExecutionTrace.duration_ms).label("total_ms"),
        )
        .where(ExecutionTrace.session_id == sid)
        .group_by(ExecutionTrace.trace_type)
    )
    rows = result.all()
    return {
        "session_id": session_id,
        "by_type": [
            {"trace_type": r.trace_type, "count": r.count, "total_ms": r.total_ms}
            for r in rows
        ],
    }
