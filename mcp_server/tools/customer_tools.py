"""Customer CRM tools exposed via MCP."""
import os
import psycopg2
from typing import Optional
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def _get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "mcpdataconnector"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def get_customers(search: Optional[str] = None, limit: int = 20) -> list[dict]:
    """
    Retrieve customers from the CRM database.

    Args:
        search: Optional search term matched against name, email, or company
        limit: Maximum number of customers to return (default 20, max 100)
    """
    limit = min(int(limit or 20), 100)
    params: list = []

    if search:
        where = "WHERE (LOWER(name) LIKE LOWER(%s) OR LOWER(email) LIKE LOWER(%s) OR LOWER(company) LIKE LOWER(%s))"
        term = f"%{search}%"
        params = [term, term, term]
    else:
        where = ""

    sql = f"""
        SELECT id, name, email, company, revenue::FLOAT, region, created_at::TEXT
        FROM customers
        {where}
        ORDER BY revenue DESC
        LIMIT %s
    """
    params.append(limit)

    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()


def add_customer(
    name: str,
    email: str,
    company: Optional[str] = None,
    revenue: float = 0.0,
    region: Optional[str] = None,
) -> dict:
    """
    Add a new customer to the CRM database.

    Args:
        name: Customer full name (required)
        email: Customer email address (required, must be unique)
        company: Company name
        revenue: Expected annual revenue
        region: Geographic region (e.g. 'North America', 'Europe')
    """
    sql = """
        INSERT INTO customers (name, email, company, revenue, region)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name, email, company, revenue::FLOAT, region, created_at::TEXT
    """
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (name, email, company, revenue or 0.0, region))
            row = cur.fetchone()
            conn.commit()
            return dict(row)
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {"error": f"Customer with email '{email}' already exists."}
    finally:
        conn.close()
