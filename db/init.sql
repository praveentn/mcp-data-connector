-- MCP Data Connector Platform - Database Schema + Seed Data

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Agents ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    agent_type TEXT NOT NULL DEFAULT 'sub',   -- 'main' | 'sub'
    capabilities JSONB NOT NULL DEFAULT '[]', -- list of tool names
    config JSONB NOT NULL DEFAULT '{}',       -- system_prompt, temperature, etc.
    parent_agent_id UUID REFERENCES agents(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Tools ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    input_schema JSONB NOT NULL DEFAULT '{}',
    mcp_endpoint TEXT,
    permission_level TEXT NOT NULL DEFAULT 'read', -- 'read' | 'write' | 'admin'
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Workflows ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    graph_definition JSONB NOT NULL DEFAULT '{}',
    trigger_agent_id UUID REFERENCES agents(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Execution Traces ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS execution_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    agent_id UUID REFERENCES agents(id),
    trace_type TEXT NOT NULL, -- 'intent_detection' | 'plan' | 'tool_call' | 'tool_result' | 'delegation' | 'response'
    payload JSONB NOT NULL DEFAULT '{}',
    tool_name TEXT,
    duration_ms INTEGER,
    status TEXT NOT NULL DEFAULT 'success', -- 'running' | 'success' | 'error'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_traces_session ON execution_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_traces_created ON execution_traces(created_at DESC);

-- ── Messages ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    role TEXT NOT NULL, -- 'user' | 'assistant'
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);

-- ── CRM: Customers ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    company TEXT,
    revenue NUMERIC(12, 2) NOT NULL DEFAULT 0,
    region TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── CRM: Sales ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    amount NUMERIC(12, 2) NOT NULL,
    product TEXT NOT NULL,
    sale_date DATE NOT NULL,
    quarter TEXT GENERATED ALWAYS AS (
        'Q' || EXTRACT(QUARTER FROM sale_date)::TEXT || ' ' || EXTRACT(YEAR FROM sale_date)::TEXT
    ) STORED
);

-- ── Seed: Default agents ──────────────────────────────────────────────────────
INSERT INTO agents (name, description, agent_type, capabilities, config) VALUES
(
    'MainOrchestrator',
    'Primary controller agent — interprets intent, plans, delegates',
    'main',
    '["query_sales_db","get_customers","add_customer","list_files","read_file"]',
    '{"system_prompt": "You are the main orchestrator agent. Break down user requests into actionable steps using available MCP tools.", "temperature": 0.1}'
),
(
    'DataQueryAgent',
    'Specialist for read-only data retrieval from the CRM database',
    'sub',
    '["query_sales_db","get_customers"]',
    '{"system_prompt": "You are a data query specialist. Use database tools to fetch accurate information.", "temperature": 0}'
),
(
    'DataWriteAgent',
    'Specialist for writing/updating CRM records',
    'sub',
    '["add_customer"]',
    '{"system_prompt": "You are a data entry specialist. Validate inputs before writing records.", "temperature": 0}'
),
(
    'FileAgent',
    'Specialist for reading and listing files from the data directory',
    'sub',
    '["list_files","read_file"]',
    '{"system_prompt": "You are a file system specialist. Navigate the data directory and return file contents.", "temperature": 0}'
)
ON CONFLICT DO NOTHING;

-- ── Seed: Tools registry ──────────────────────────────────────────────────────
INSERT INTO tools (name, description, input_schema, permission_level) VALUES
(
    'query_sales_db',
    'Query the sales database with optional filters. Returns sales records joined with customer data.',
    '{"type":"object","properties":{"product":{"type":"string","description":"Filter by product name (partial match)"},"min_amount":{"type":"number","description":"Minimum sale amount"},"limit":{"type":"integer","description":"Max rows to return","default":10}},"required":[]}',
    'read'
),
(
    'get_customers',
    'Retrieve customers from the CRM. Supports search by name/email and pagination.',
    '{"type":"object","properties":{"search":{"type":"string","description":"Search term for name or email"},"limit":{"type":"integer","description":"Max customers to return","default":20}},"required":[]}',
    'read'
),
(
    'add_customer',
    'Add a new customer to the CRM database.',
    '{"type":"object","properties":{"name":{"type":"string"},"email":{"type":"string"},"company":{"type":"string"},"revenue":{"type":"number"},"region":{"type":"string"}},"required":["name","email"]}',
    'write'
),
(
    'list_files',
    'List files available in the data directory.',
    '{"type":"object","properties":{"directory":{"type":"string","description":"Subdirectory to list (relative to data root)","default":"."}},"required":[]}',
    'read'
),
(
    'read_file',
    'Read the content of a file from the data directory.',
    '{"type":"object","properties":{"filepath":{"type":"string","description":"Path to the file (relative to data root)"}},"required":["filepath"]}',
    'read'
)
ON CONFLICT (name) DO NOTHING;

-- ── Seed: Sample customers ────────────────────────────────────────────────────
INSERT INTO customers (name, email, company, revenue, region) VALUES
('Alice Johnson',   'alice@acme.com',       'Acme Corp',        125000, 'North America'),
('Bob Smith',       'bob@globex.com',        'Globex Inc',       98000,  'Europe'),
('Carol Williams',  'carol@initech.com',     'Initech',          210000, 'North America'),
('David Brown',     'david@hooli.com',       'Hooli',            75000,  'Asia Pacific'),
('Eva Martinez',    'eva@umbrella.com',      'Umbrella Corp',    310000, 'Latin America'),
('Frank Lee',       'frank@vehement.com',    'Vehement Capital', 450000, 'North America'),
('Grace Kim',       'grace@piedpiper.com',   'Pied Piper',       55000,  'North America'),
('Henry Chen',      'henry@dunder.com',      'Dunder Mifflin',   88000,  'North America'),
('Isabel Torres',   'isabel@sabre.com',      'Sabre',            195000, 'Europe'),
('James Wilson',    'james@vandelay.com',    'Vandelay Ind.',    320000, 'Asia Pacific')
ON CONFLICT (email) DO NOTHING;

-- ── Seed: Sample sales ────────────────────────────────────────────────────────
INSERT INTO sales (customer_id, amount, product, sale_date)
SELECT c.id, s.amount, s.product, s.sale_date
FROM (VALUES
    ('alice@acme.com',      12500,  'Enterprise License',  '2024-01-15'),
    ('alice@acme.com',      8400,   'Support Package',     '2024-03-20'),
    ('bob@globex.com',      22000,  'Platform Subscription','2024-02-10'),
    ('carol@initech.com',   45000,  'Enterprise License',  '2024-01-28'),
    ('carol@initech.com',   15000,  'Professional Services','2024-04-05'),
    ('david@hooli.com',     9800,   'Starter Plan',        '2024-03-01'),
    ('eva@umbrella.com',    68000,  'Enterprise License',  '2024-01-10'),
    ('eva@umbrella.com',    32000,  'Platform Subscription','2024-04-15'),
    ('frank@vehement.com',  95000,  'Enterprise License',  '2024-02-20'),
    ('frank@vehement.com',  28000,  'Professional Services','2024-03-30'),
    ('grace@piedpiper.com', 5500,   'Starter Plan',        '2024-01-05'),
    ('henry@dunder.com',    11000,  'Support Package',     '2024-02-14'),
    ('isabel@sabre.com',    42000,  'Platform Subscription','2024-03-22'),
    ('james@wilson.com',    78000,  'Enterprise License',  '2024-04-01'),
    ('james@vandelay.com',  35000,  'Professional Services','2024-02-28'),
    ('alice@acme.com',      18000,  'Platform Subscription','2024-04-10'),
    ('bob@globex.com',      7500,   'Support Package',     '2024-04-18'),
    ('carol@initech.com',   55000,  'Enterprise License',  '2024-04-25'),
    ('frank@vehement.com',  41000,  'Platform Subscription','2024-03-15'),
    ('isabel@sabre.com',    19000,  'Support Package',     '2024-04-20')
) AS s(email, amount, product, sale_date)
JOIN customers c ON c.email = s.email
ON CONFLICT DO NOTHING;
