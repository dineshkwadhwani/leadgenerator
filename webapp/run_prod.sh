#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_DIR="$PWD"
VENV_ACTIVATE="$APP_DIR/../.venv/bin/activate"
PID_FILE="$APP_DIR/.server.pid"
LOG_FILE="$APP_DIR/server.log"

ensure_venv() {
  if [[ ! -f "$VENV_ACTIVATE" ]]; then
    echo "Virtual environment not found at $VENV_ACTIVATE"
    echo "Create it first: python3 -m venv ../.venv"
    exit 1
  fi
}

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

start_background() {
  ensure_venv

  if is_running; then
    echo "Server already running with PID $(cat "$PID_FILE")"
    exit 0
  fi

  source "$VENV_ACTIVATE"
  nohup python app.py >>"$LOG_FILE" 2>&1 &
  echo "$!" >"$PID_FILE"
  disown || true

  echo "Server started in background"
  echo "PID: $(cat "$PID_FILE")"
  echo "Logs: $LOG_FILE"
}

stop_server() {
  if is_running; then
    local pid
    pid="$(cat "$PID_FILE")"
    kill "$pid"
    rm -f "$PID_FILE"
    echo "Stopped server PID $pid"
  else
    rm -f "$PID_FILE"
    echo "Server is not running"
  fi
}

status_server() {
  if is_running; then
    echo "Server is running with PID $(cat "$PID_FILE")"
  else
    echo "Server is not running"
    exit 1
  fi
}

show_logs() {
  touch "$LOG_FILE"
  tail -n 100 "$LOG_FILE"
}

follow_logs() {
  touch "$LOG_FILE"
  tail -f "$LOG_FILE"
}

usage() {
  cat <<'EOF'
Usage: ./run_prod.sh [command]

Commands:
  up            Run in background (default)
  stop          Stop background server
  restart       Restart background server
  status        Show server status
  logs          Show last 100 log lines
  follow-logs   Stream logs
EOF
}

case "${1:-up}" in
  up)
    start_background
    ;;
  stop)
    stop_server
    ;;
  restart)
    stop_server
    start_background
    ;;
  status)
    status_server
    ;;
  logs)
    show_logs
    ;;
  follow-logs)
    follow_logs
    ;;
  *)
    usage
    exit 1
    ;;
esac
