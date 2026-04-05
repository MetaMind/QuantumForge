#!/usr/bin/env bash
# start_all.sh — Start backend and frontend, auto-selecting free ports

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$SCRIPT_DIR/.quantumforge.pids"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$LOG_DIR"

# ── Detect venv ────────────────────────────────────────────────────────────────
# Look for venv one level up (../venv) or inside the project (./venv)
if [[ -f "$ROOT_DIR/venv/bin/python3" ]]; then
  PYTHON="$ROOT_DIR/venv/bin/python3"
elif [[ -f "$(dirname "$ROOT_DIR")/venv/bin/python3" ]]; then
  PYTHON="$(dirname "$ROOT_DIR")/venv/bin/python3"
else
  PYTHON="$(command -v python3)"
fi
echo "Using Python: $PYTHON"

# ── helpers ────────────────────────────────────────────────────────────────────

find_free_port() {
  local port=$1
  while lsof -iTCP:"$port" -sTCP:LISTEN -t &>/dev/null 2>&1; do
    echo "  Port $port is in use, trying $((port + 1))..." >&2
    port=$((port + 1))
  done
  echo "$port"
}

# ── backend ────────────────────────────────────────────────────────────────────

BACKEND_DEFAULT=8000
BACKEND_PORT=$(find_free_port $BACKEND_DEFAULT)

echo "Starting backend on port $BACKEND_PORT..."

cd "$ROOT_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"

PORT=$BACKEND_PORT "$PYTHON" -m uvicorn backend.main:create_app \
  --host 0.0.0.0 \
  --port "$BACKEND_PORT" \
  --workers 1 \
  > "$BACKEND_LOG" 2>&1 &

BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID  (log: $BACKEND_LOG)"

# ── frontend ───────────────────────────────────────────────────────────────────

FRONTEND_DEFAULT=3001
FRONTEND_PORT=$(find_free_port $FRONTEND_DEFAULT)

echo "Starting frontend on port $FRONTEND_PORT..."

FRONTEND_LOG="$LOG_DIR/frontend.log"

cd "$ROOT_DIR/frontend"
VITE_PORT=$FRONTEND_PORT npx vite --port "$FRONTEND_PORT" --host 0.0.0.0 \
  > "$FRONTEND_LOG" 2>&1 &

FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID  (log: $FRONTEND_LOG)"

# ── save pids ──────────────────────────────────────────────────────────────────

cat > "$PID_FILE" <<EOF
BACKEND_PID=$BACKEND_PID
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PID=$FRONTEND_PID
FRONTEND_PORT=$FRONTEND_PORT
EOF

echo ""
echo "All services started."
echo "  Backend  → http://localhost:$BACKEND_PORT"
echo "  Frontend → http://localhost:$FRONTEND_PORT"
echo ""
echo "Run scripts/stop_all.sh to stop everything."
