#!/bin/bash
# uCore Startup Script — Self-healing auto-start for snackbar services
# This script ensures all uCore services are running at login

set -e

UCORE_ROOT="${UCORE_ROOT:-$HOME/Code/uCore}"
BACKEND_DIR="$UCORE_ROOT/backend"
LOG_DIR="$HOME/.ucore/logs"
PID_DIR="$HOME/.ucore"

# Ensure directories exist
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_DIR/ucore-startup.log"
}

log "🚀 Starting uCore services..."

# Check if backend is running
check_backend() {
    curl -s --max-time 2 "http://localhost:8484/api/health" > /dev/null 2>&1
}

# Check if menu is running
check_menu() {
    pgrep -f "app.menu.unified_menu" > /dev/null 2>&1
}

# Start backend if not running
if ! check_backend; then
    log "🔧 Starting snackbar backend..."
    if [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
        PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
    else
        PYTHON_BIN="/usr/bin/python3"
    fi
    
    cd "$BACKEND_DIR" && PYTHONPATH=. $PYTHON_BIN -m app --port 8484 > "$LOG_DIR/ucore-server.log" 2>&1 &
    sleep 3
    
    if check_backend; then
        log "✅ Backend started successfully"
    else
        log "❌ Backend failed to start"
    fi
fi

# Start menu if not running
if ! check_menu; then
    log "🔧 Starting uCore menu..."
    if [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
        PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
    else
        PYTHON_BIN="/usr/bin/python3"
    fi
    
    cd "$BACKEND_DIR" && PYTHONPATH=. $PYTHON_BIN -m app.menu.unified_menu_simple > "$LOG_DIR/ucore-menu.log" 2>&1 &
    sleep 2
    
    if check_menu; then
        log "✅ Menu started successfully"
    else
        log "❌ Menu failed to start"
    fi
fi

# Run health check skill
log "🏥 Running health check..."
if check_backend; then
    curl -s --max-time 5 "http://localhost:8484/api/skills/autostart_health_check/run" > /dev/null 2>&1 || true
fi

log "✅ uCore startup complete"