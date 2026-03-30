#!/usr/bin/env bash
# MCP Data Connector Platform — local dev startup script
# Requires: colima (or Docker Desktop), Python 3.11+, Node.js 18+

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

log()  { echo -e "${CYAN}[mcp]${NC} $*"; }
ok()   { echo -e "${GREEN}[ok]${NC}  $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
err()  { echo -e "${RED}[err]${NC}  $*"; }

# ── Env ───────────────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  warn ".env not found — copying from .env.example"
  cp .env.example .env
fi
source .env

BACKEND_PORT="${BACKEND_PORT:-7790}"
FRONTEND_PORT="${FRONTEND_PORT:-7791}"
MCP_SERVER_PORT="${MCP_SERVER_PORT:-7792}"
MCP_INSPECTOR_PORT="${MCP_INSPECTOR_PORT:-6274}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

# ── Kill existing processes on our ports ──────────────────────────────────────
log "Clearing ports $BACKEND_PORT $FRONTEND_PORT $MCP_SERVER_PORT $MCP_INSPECTOR_PORT..."
for port in $BACKEND_PORT $FRONTEND_PORT $MCP_SERVER_PORT $MCP_INSPECTOR_PORT; do
  lsof -ti tcp:"$port" | xargs -r kill -9 2>/dev/null || true
done

# ── Python venv ───────────────────────────────────────────────────────────────
if [ ! -d .venv ]; then
  log "Creating Python virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

log "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "Python deps installed"

# ── Colima / Docker ───────────────────────────────────────────────────────────
if command -v colima &>/dev/null; then
  if ! colima status 2>/dev/null | grep -q "Running"; then
    log "Starting Colima..."
    colima start
  fi
  ok "Colima running"
fi

# ── PostgreSQL via Docker ──────────────────────────────────────────────────────
log "Starting PostgreSQL container..."
docker compose up -d postgres

log "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
  if docker compose exec -T postgres pg_isready -U postgres &>/dev/null; then
    ok "PostgreSQL ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    err "PostgreSQL did not start in time"
    exit 1
  fi
  sleep 1
done

# ── Ensure data/files directory ───────────────────────────────────────────────
mkdir -p data/files

# ── MCP Server ────────────────────────────────────────────────────────────────
log "Starting MCP Server on port $MCP_SERVER_PORT..."
PYTHONPATH="$ROOT" python mcp_server/server.py \
  > /tmp/mcp_server.log 2>&1 &
MCP_PID=$!
echo "$MCP_PID" > /tmp/mcp_server.pid
sleep 2
if kill -0 "$MCP_PID" 2>/dev/null; then
  ok "MCP Server running (pid=$MCP_PID)"
else
  err "MCP Server failed to start — check /tmp/mcp_server.log"
  cat /tmp/mcp_server.log
  exit 1
fi

# ── Backend ───────────────────────────────────────────────────────────────────
log "Starting Backend (FastAPI) on port $BACKEND_PORT..."
PYTHONPATH="$ROOT" uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port "$BACKEND_PORT" \
  --reload \
  --log-level info \
  > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > /tmp/backend.pid
sleep 3
if kill -0 "$BACKEND_PID" 2>/dev/null; then
  ok "Backend running (pid=$BACKEND_PID)"
else
  err "Backend failed to start — check /tmp/backend.log"
  cat /tmp/backend.log
  exit 1
fi

# ── Frontend ──────────────────────────────────────────────────────────────────
log "Installing frontend dependencies..."
cd frontend
if [ ! -d node_modules ]; then
  # Temporarily suspend exit-on-error for npm install (cache permission issues are non-fatal)
  set +e
  npm install 2>&1
  NPM_EXIT=$?
  set -e
  if [ $NPM_EXIT -ne 0 ]; then
    warn "npm install exited with $NPM_EXIT — attempting to fix cache ownership..."
    chown -R "$(id -u):$(id -g)" "$HOME/.npm" 2>/dev/null || true
    npm install
  fi
fi
ok "Frontend deps installed"

log "Starting React dev server on port $FRONTEND_PORT..."
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > /tmp/frontend.pid
cd "$ROOT"
sleep 3
if kill -0 "$FRONTEND_PID" 2>/dev/null; then
  ok "Frontend running (pid=$FRONTEND_PID)"
else
  err "Frontend failed to start — check /tmp/frontend.log"
  cat /tmp/frontend.log
  exit 1
fi

# ── MCP Inspector ─────────────────────────────────────────────────────────────
if command -v npx &>/dev/null; then
  log "Starting MCP Inspector..."
  # DANGEROUSLY_OMIT_AUTH disables the proxy token — fine for local dev
  DANGEROUSLY_OMIT_AUTH=true \
  PORT="$MCP_INSPECTOR_PORT" \
  npx -y @modelcontextprotocol/inspector \
    > /tmp/mcp_inspector.log 2>&1 &
  INSPECTOR_PID=$!
  sleep 3
  if kill -0 "$INSPECTOR_PID" 2>/dev/null; then
    ok "MCP Inspector running (pid=$INSPECTOR_PID)"
  else
    warn "MCP Inspector did not start (optional) — check /tmp/mcp_inspector.log"
  fi
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      MCP Data Connector Platform — Running       ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}  Frontend:      http://localhost:${FRONTEND_PORT}          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Backend API:   http://localhost:${BACKEND_PORT}          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  API Docs:      http://localhost:${BACKEND_PORT}/docs     ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  MCP Server:    http://localhost:${MCP_SERVER_PORT}/sse   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Inspector UI:  http://localhost:${MCP_INSPECTOR_PORT}         ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}MCP Inspector — how to connect:${NC}"
echo "  1. Open http://localhost:${MCP_INSPECTOR_PORT}"
echo "  2. Change Transport Type  →  SSE"
echo "  3. Set URL                →  http://localhost:${MCP_SERVER_PORT}/sse"
echo "  4. Click Connect"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  Backend:     tail -f /tmp/backend.log"
echo "  MCP Server:  tail -f /tmp/mcp_server.log"
echo "  Frontend:    tail -f /tmp/frontend.log"
echo ""
echo -e "${YELLOW}Stop all:${NC}  kill \$(cat /tmp/backend.pid /tmp/mcp_server.pid /tmp/frontend.pid)"
echo ""

# Keep alive — wait for any foreground process
wait
