"""Audit logging middleware for MCP tool calls."""
import os
import time
import uuid
import logging
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "mcpdataconnector"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def log_tool_call(
    tool_name: str,
    inputs: dict,
    outputs,
    duration_ms: int,
    status: str = "success",
    agent_id: str = None,
    session_id: str = None,
):
    """Persist an MCP tool call audit record to the database."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO execution_traces
                    (id, session_id, agent_id, trace_type, payload, tool_name, duration_ms, status)
                VALUES
                    (%s, %s, %s, 'tool_call', %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    session_id or str(uuid.uuid4()),
                    agent_id,
                    Json({
                        "inputs": inputs,
                        "output": str(outputs)[:2000] if outputs else None,
                    }),
                    tool_name,
                    duration_ms,
                    status,
                ),
            )
            conn.commit()
    except Exception as exc:
        logger.warning("Audit log failed for tool %s: %s", tool_name, exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def audited(fn):
    """Decorator that wraps a tool function with audit logging."""
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        status = "success"
        result = None
        try:
            result = fn(*args, **kwargs)
            return result
        except Exception as exc:
            status = "error"
            result = str(exc)
            raise
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            log_tool_call(
                tool_name=fn.__name__,
                inputs=kwargs,
                outputs=result,
                duration_ms=duration_ms,
                status=status,
            )
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper
