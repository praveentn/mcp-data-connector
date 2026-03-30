"""Sales database query tools exposed via MCP."""
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


def query_sales_db(
    product: Optional[str] = None,
    min_amount: Optional[float] = None,
    region: Optional[str] = None,
    quarter: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """
    Query the sales database. Returns sales records joined with customer info.

    Args:
        product: Filter by product name (partial match, case-insensitive)
        min_amount: Minimum sale amount filter
        region: Filter by customer region (exact match)
        quarter: Filter by quarter string e.g. 'Q1 2024'
        limit: Maximum number of records to return (default 10, max 50)
    """
    limit = min(int(limit or 10), 50)

    conditions = []
    params: list = []

    if product:
        conditions.append("LOWER(s.product) LIKE LOWER(%s)")
        params.append(f"%{product}%")
    if min_amount is not None:
        conditions.append("s.amount >= %s")
        params.append(float(min_amount))
    if region:
        conditions.append("c.region = %s")
        params.append(region)
    if quarter:
        conditions.append("s.quarter = %s")
        params.append(quarter)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT
            s.id,
            s.amount,
            s.product,
            s.sale_date::TEXT,
            s.quarter,
            c.name  AS customer_name,
            c.email AS customer_email,
            c.company,
            c.region
        FROM sales s
        JOIN customers c ON c.id = s.customer_id
        {where_clause}
        ORDER BY s.sale_date DESC
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
