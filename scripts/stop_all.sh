#!/usr/bin/env bash
# stop_all.sh — Stop backend and frontend started by start_all.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.quantumforge.pids"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No PID file found at $PID_FILE — nothing to stop."
  exit 0
fi

source "$PID_FILE"

stop_process() {
  local name=$1
  local pid=$2
  local port=$3

  if [[ -z "$pid" ]]; then
    echo "$name: no PID recorded, skipping."
    return
  fi

  if kill -0 "$pid" 2>/dev/null; then
    echo "Stopping $name (PID $pid, port $port)..."
    kill "$pid"
    # Wait up to 5s for clean exit, then force-kill
    for i in {1..10}; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "  Force-killing $name..."
      kill -9 "$pid"
    fi
    echo "  $name stopped."
  else
    echo "$name (PID $pid) is not running."
    # Clean up any stray process still holding the port
    if [[ -n "$port" ]]; then
      local stray
      stray=$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)
      if [[ -n "$stray" ]]; then
        echo "  Killing stray process on port $port (PID $stray)..."
        kill "$stray" 2>/dev/null || kill -9 "$stray" 2>/dev/null || true
      fi
    fi
  fi
}

stop_process "Backend"  "$BACKEND_PID"  "$BACKEND_PORT"
stop_process "Frontend" "$FRONTEND_PID" "$FRONTEND_PORT"

rm -f "$PID_FILE"
echo ""
echo "All services stopped."
