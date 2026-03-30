"""
MCP Data Connector Server

Exposes CRM and file-system tools via the Model Context Protocol (FastMCP).
Run with: python mcp_server/server.py
Inspector:  npx @modelcontextprotocol/inspector http://localhost:7792/sse
"""
import os
import sys
import logging
from typing import Optional
from dotenv import load_dotenv
from fastmcp import FastMCP

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Instantiate FastMCP ───────────────────────────────────────────────────────
mcp = FastMCP(
    name="MCP Data Connector",
    instructions=(
        "You are a data connector MCP server. "
        "Expose CRM database tools and file-system tools to AI agents. "
        "Always return structured data. Never expose raw SQL errors to callers."
    ),
)

# ── Import connectors ─────────────────────────────────────────────────────────
from mcp_server.tools.sales_tools import query_sales_db as _query_sales_db
from mcp_server.tools.customer_tools import get_customers as _get_customers
from mcp_server.tools.customer_tools import add_customer as _add_customer
from mcp_server.tools.file_tools import list_files as _list_files
from mcp_server.tools.file_tools import read_file as _read_file


# ── Register tools ────────────────────────────────────────────────────────────

@mcp.tool()
def query_sales_db(
    product: Optional[str] = None,
    min_amount: Optional[float] = None,
    region: Optional[str] = None,
    quarter: Optional[str] = None,
    limit: int = 10,
) -> list:
    """
    Query the sales database. Returns sales records joined with customer info.

    Args:
        product: Filter by product name (partial match, case-insensitive)
        min_amount: Minimum sale amount filter
        region: Filter by customer region (e.g. 'North America', 'Europe')
        quarter: Filter by quarter string e.g. 'Q1 2024'
        limit: Maximum number of records to return (default 10, max 50)
    """
    logger.info("Tool: query_sales_db | product=%s min_amount=%s region=%s", product, min_amount, region)
    return _query_sales_db(
        product=product,
        min_amount=min_amount,
        region=region,
        quarter=quarter,
        limit=limit,
    )


@mcp.tool()
def get_customers(search: Optional[str] = None, limit: int = 20) -> list:
    """
    Retrieve customers from the CRM database.

    Args:
        search: Optional search term matched against name, email, or company
        limit: Maximum number of customers to return (default 20, max 100)
    """
    logger.info("Tool: get_customers | search=%s limit=%s", search, limit)
    return _get_customers(search=search, limit=limit)


@mcp.tool()
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
    logger.info("Tool: add_customer | name=%s email=%s", name, email)
    return _add_customer(name=name, email=email, company=company, revenue=revenue, region=region)


@mcp.tool()
def list_files(directory: str = ".") -> list:
    """
    List files in the data directory.

    Args:
        directory: Subdirectory to list relative to the data root (default '.')
    """
    logger.info("Tool: list_files | directory=%s", directory)
    return _list_files(directory=directory)


@mcp.tool()
def read_file(filepath: str) -> dict:
    """
    Read the content of a file from the data directory.

    Args:
        filepath: Path to the file relative to the data root (e.g. 'q4_sales_summary.md')
    """
    logger.info("Tool: read_file | filepath=%s", filepath)
    return _read_file(filepath=filepath)


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("data://schema/customers")
def customers_schema() -> str:
    """Returns the schema of the customers table."""
    return """
    TABLE: customers
    COLUMNS:
      id       SERIAL PRIMARY KEY
      name     TEXT NOT NULL
      email    TEXT UNIQUE NOT NULL
      company  TEXT
      revenue  NUMERIC(12,2)
      region   TEXT  -- values: 'North America', 'Europe', 'Asia Pacific', 'Latin America'
      created_at TIMESTAMPTZ
    """


@mcp.resource("data://schema/sales")
def sales_schema() -> str:
    """Returns the schema of the sales table."""
    return """
    TABLE: sales
    COLUMNS:
      id          SERIAL PRIMARY KEY
      customer_id INT REFERENCES customers(id)
      amount      NUMERIC(12,2)
      product     TEXT  -- values: 'Enterprise License', 'Platform Subscription', 'Professional Services', 'Support Package', 'Starter Plan'
      sale_date   DATE
      quarter     TEXT GENERATED (e.g. 'Q1 2024')
    """


# ── Prompts ───────────────────────────────────────────────────────────────────

@mcp.prompt()
def sales_analysis_prompt(time_period: str = "last quarter") -> str:
    """Prompt template for analysing sales performance."""
    return (
        f"You are a sales analyst. Analyse the sales data for {time_period}.\n"
        "Steps:\n"
        "1. Use query_sales_db to fetch recent sales records.\n"
        "2. Identify top products by revenue.\n"
        "3. Break down performance by region.\n"
        "4. Highlight the top 3 customers.\n"
        "5. Summarise key insights and recommend next actions."
    )


@mcp.prompt()
def customer_research_prompt(customer_name: Optional[str] = "Alice Johnson") -> str:
    """Prompt template for researching a specific customer."""
    return (
        f"Research the customer '{customer_name}' in the CRM.\n"
        "Steps:\n"
        f"1. Use get_customers with search='{customer_name}' to find their record.\n"
        "2. Use query_sales_db to find all their purchases.\n"
        "3. Calculate their total lifetime value.\n"
        "4. Summarise their buying patterns and suggest upsell opportunities."
    )


@mcp.prompt()
def onboard_customer_prompt(
    name: Optional[str] = "Jane Doe",
    email: Optional[str] = "jane@example.com",
    company: Optional[str] = "",
) -> str:
    """Prompt template for onboarding a new customer."""
    return (
        f"Onboard a new customer to the CRM.\n"
        f"Customer details: name='{name}', email='{email}', company='{company}'.\n"
        "Steps:\n"
        "1. Use add_customer to create the record.\n"
        "2. Confirm the customer was created successfully.\n"
        "3. Suggest a follow-up action based on the company profile."
    )


@mcp.prompt()
def file_report_prompt(filename: str = "") -> str:
    """Prompt template for reading and summarising a report file."""
    step = f"read_file with filepath='{filename}'" if filename else "list_files to discover available reports, then read_file on the most relevant one"
    return (
        f"Retrieve and summarise a report from the data directory.\n"
        f"Steps:\n"
        f"1. Use {step}.\n"
        "2. Extract the key metrics and findings.\n"
        "3. Present a concise executive summary (3-5 bullet points)."
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "7792"))
    logger.info("Starting MCP Data Connector on port %d (SSE transport)", port)
    logger.info("Inspector: npx @modelcontextprotocol/inspector http://localhost:%d/sse", port)
    mcp.run(transport="sse", host="0.0.0.0", port=port)
