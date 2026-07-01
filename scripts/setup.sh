#!/bin/bash
# setup.sh — uCore Development Setup
# Installs all dependencies and configures launchd agents for auto-start.
# Run this after cloning the repo for the first time.
#
# Usage: ./scripts/setup.sh [--help] [--uninstall]
#
# This script:
#   1. Checks prerequisites (Python 3.11+, Node 22+, pnpm)
#   2. Creates Python virtual environment
#   3. Installs Python dependencies (editable mode)
#   4. Installs Node.js dependencies via pnpm
#   5. Builds the Vue frontend
#   6. Creates ~/.ucore/ directory structure
#   7. Installs launchd agents for auto-start
#   8. Sets up UDOS_ROOT environment variable

set -euo pipefail

UCORE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$UCORE_ROOT/backend"
FRONTEND_DIR="$UCORE_ROOT/frontend-vue"
VENV_DIR="$BACKEND_DIR/.venv"
LOG_DIR="$HOME/.ucore/logs"
DATA_DIR="$HOME/.ucore/data"
CONFIG_DIR="$HOME/.ucore/config"

# ─── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Help ────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--help" ]]; then
    cat <<EOF
uCore Setup Script — Development Environment Setup

Usage: ./scripts/setup.sh [OPTIONS]

Options:
  --help        Show this help message
  --uninstall   Remove all uCore components and launchd agents

This script sets up the uCore development environment including:
  - Python virtual environment with all dependencies
  - Node.js dependencies via pnpm
  - Vue frontend build
  - macOS launchd agents for auto-start
  - ~/.ucore/ data directory structure

Prerequisites:
  - Python 3.11 or later
  - Node.js 22 or later
  - pnpm 9 or later
EOF
    exit 0
fi

# ─── Uninstall ───────────────────────────────────────────────────────

if [[ "${1:-}" == "--uninstall" ]]; then
    echo ""
    info "Starting uCore uninstall..."
    echo ""

    # Remove launchd agents
    info "Removing launchd agents..."
    launchctl bootout gui/$(id -u)/com.udos.ucore-menu 2>/dev/null || true
    launchctl bootout gui/$(id -u)/com.udos.ucore-server 2>/dev/null || true
    launchctl bootout gui/$(id -u)/com.udos.ucore-frontend 2>/dev/null || true
    rm -f "$HOME/Library/LaunchAgents/com.udos.ucore-menu.plist"
    rm -f "$HOME/Library/LaunchAgents/com.udos.ucore-server.plist"
    rm -f "$HOME/Library/LaunchAgents/com.udos.ucore-frontend.plist"
    ok "Launchd agents removed"

    # Remove ~/.ucore/ data directory
    if [[ -d "$HOME/.ucore" ]]; then
        info "Removing ~/.ucore/ data directory..."
        rm -rf "$HOME/.ucore"
        ok "~/.ucore/ removed"
    fi

    # Remove UDOS_ROOT from .zshrc
    if grep -q 'export UDOS_ROOT=' "$HOME/.zshrc" 2>/dev/null; then
        info "Removing UDOS_ROOT from .zshrc..."
        sed -i '' '/export UDOS_ROOT=/d' "$HOME/.zshrc"
        sed -i '' '/export ROOT=/d' "$HOME/.zshrc"
        ok "UDOS_ROOT removed from .zshrc"
    fi

    echo ""
    ok "uCore uninstall complete"
    echo ""
    info "Note: Python venv at $VENV_DIR and node_modules were NOT removed."
    info "To remove them manually:"
    info "  rm -rf $VENV_DIR"
    info "  rm -rf $UCORE_ROOT/node_modules $FRONTEND_DIR/node_modules"
    exit 0
fi

# ─── Banner ──────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       uCore Setup — v4.0.0              ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ─── Prerequisites Check ─────────────────────────────────────────────

info "Checking prerequisites..."

# Python
PYTHON_BIN=""
for cmd in python3.14 python3.13 python3.12 python3.11 python3; do
    if command -v "$cmd" &>/dev/null; then
        PY_VER=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PY_MAJOR=${PY_VER%%.*}
        PY_MINOR=${PY_VER#*.}
        if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 11 ]]; then
            PYTHON_BIN="$cmd"
            break
        fi
    fi
done

if [[ -z "$PYTHON_BIN" ]]; then
    err "Python 3.11+ is required. Install it with: brew install python@3.14"
    exit 1
fi
ok "Python: $($PYTHON_BIN --version 2>&1)"

# Node.js
if ! command -v node &>/dev/null; then
    err "Node.js is required. Install it with: brew install node@22"
    exit 1
fi
NODE_VER=$(node --version 2>&1 | grep -oE '[0-9]+' | head -1)
if [[ "$NODE_VER" -lt 22 ]]; then
    err "Node.js 22+ is required. Found: $(node --version)"
    exit 1
fi
ok "Node.js: $(node --version)"

# pnpm
if ! command -v pnpm &>/dev/null; then
    err "pnpm is required. Install it with: brew install pnpm"
    exit 1
fi
PNPM_VER=$(pnpm --version 2>&1 | grep -oE '^[0-9]+' | head -1)
if [[ "$PNPM_VER" -lt 9 ]]; then
    err "pnpm 9+ is required. Found: $(pnpm --version)"
    exit 1
fi
ok "pnpm: $(pnpm --version)"

# ─── Create Directory Structure ──────────────────────────────────────

info "Creating ~/.ucore/ directory structure..."
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$CONFIG_DIR"
ok "Directory structure created"

# ─── Python Virtual Environment ──────────────────────────────────────

if [[ -f "$VENV_DIR/bin/python" ]]; then
    info "Python venv already exists at $VENV_DIR"
else
    info "Creating Python virtual environment..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    ok "Virtual environment created at $VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install uCore and dependencies in editable mode
info "Installing Python dependencies..."
cd "$BACKEND_DIR"

# Install build deps first
pip install --quiet --upgrade pip setuptools wheel 2>&1 | tail -1

# Install uCore in editable mode (installs dependencies from pyproject.toml)
pip install --quiet -e . 2>&1 | tail -1
ok "uCore Python package installed"

# Install dev dependencies
pip install --quiet -e ".[dev]" 2>&1 | tail -1 || true
ok "Dev dependencies installed"

# Install snackmachine and other pip packages from vendor
if [[ -f "$UCORE_ROOT/vendor/sources.yaml" ]]; then
    info "Checking vendor packages..."
    # snackmachine, udos-budget, udos-agents, udos-identity
    for pkg in snackmachine udos-budget udos-agents udos-identity; do
        if python -c "import $pkg" 2>/dev/null; then
            ok "  $pkg already installed"
        else
            warn "  $pkg not found — install from: https://github.com/uDosGo/$pkg"
        fi
    done
fi

cd "$UCORE_ROOT"

# ─── Node.js Dependencies ────────────────────────────────────────────

if [[ -d "$UCORE_ROOT/node_modules" ]] && [[ -d "$FRONTEND_DIR/node_modules" ]]; then
    info "Node.js dependencies already installed"
else
    info "Installing Node.js dependencies via pnpm..."
    pnpm install 2>&1 | tail -3
    ok "Node.js dependencies installed"
fi

# ─── Build Frontend ──────────────────────────────────────────────────

if [[ -d "$FRONTEND_DIR/dist" ]]; then
    info "Frontend already built"
else
    info "Building Vue frontend..."
    cd "$FRONTEND_DIR"
    pnpm build 2>&1 | tail -3
    cd "$UCORE_ROOT"
    ok "Frontend built at $FRONTEND_DIR/dist"
fi

# ─── Set UDOS_ROOT ───────────────────────────────────────────────────

if ! grep -q 'export UDOS_ROOT=' "$HOME/.zshrc" 2>/dev/null; then
    info "Setting UDOS_ROOT in ~/.zshrc..."
    echo "" >> "$HOME/.zshrc"
    echo "# uCore — UDOS_ROOT" >> "$HOME/.zshrc"
    echo 'export UDOS_ROOT="$HOME/Code"' >> "$HOME/.zshrc"
    echo 'export ROOT="$UDOS_ROOT"' >> "$HOME/.zshrc"
    ok "UDOS_ROOT set in ~/.zshrc"
else
    info "UDOS_ROOT already set in ~/.zshrc"
fi

# ─── Install Launchd Agents ──────────────────────────────────────────

info "Installing launchd agents..."

# Menu agent
if [[ -f "$HOME/Library/LaunchAgents/com.udos.ucore-menu.plist" ]]; then
    info "Menu launchd agent already installed"
else
    bash "$UCORE_ROOT/scripts/install_ucore_menu_launchd.sh"
    ok "Menu launchd agent installed"
fi

# Server agent
SERVER_PLIST="$HOME/Library/LaunchAgents/com.udos.ucore-server.plist"
if [[ -f "$SERVER_PLIST" ]]; then
    info "Server launchd agent already installed"
else
    # Create server plist
    cat > "$SERVER_PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.udos.ucore-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_DIR/bin/python</string>
        <string>-m</string>
        <string>app.core.snackbar</string>
        <string>--port</string>
        <string>8484</string>
        <string>--auto-start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$BACKEND_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/ucore-server-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/ucore-server-stderr.log</string>
    <key>TimeOut</key>
    <integer>60</integer>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>PYTHONPATH</key>
        <string>$BACKEND_DIR</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
        <key>UCORE_DEBUG</key>
        <string>1</string>
    </dict>
</dict>
</plist>
PLISTEOF
    launchctl bootstrap "gui/$(id -u)" "$SERVER_PLIST" 2>/dev/null || true
    ok "Server launchd agent installed"
fi

# Frontend agent
FRONTEND_PLIST="$HOME/Library/LaunchAgents/com.udos.ucore-frontend.plist"
if [[ -f "$FRONTEND_PLIST" ]]; then
    info "Frontend launchd agent already installed"
else
    cat > "$FRONTEND_PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.udos.ucore-frontend</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-lc</string>
        <string>pnpm --filter @udos/ui-hub-vue run dev --host 127.0.0.1 --port 5175</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$UCORE_ROOT</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/ucore-frontend-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/ucore-frontend-stderr.log</string>
    <key>TimeOut</key>
    <integer>60</integer>
    <key>EnvironmentVariables</key>
    <dict>
        <key>UCORE_DEBUG</key>
        <string>1</string>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
PLISTEOF
    launchctl bootstrap "gui/$(id -u)" "$FRONTEND_PLIST" 2>/dev/null || true
    ok "Frontend launchd agent installed"
fi

# ─── Start Services ──────────────────────────────────────────────────

info "Starting services..."
launchctl kickstart "gui/$(id -u)/com.udos.ucore-server" 2>/dev/null || true
sleep 2
launchctl kickstart "gui/$(id -u)/com.udos.ucore-menu" 2>/dev/null || true
launchctl kickstart "gui/$(id -u)/com.udos.ucore-frontend" 2>/dev/null || true

# ─── Verify ──────────────────────────────────────────────────────────

echo ""
info "Verifying services..."
sleep 2

# Check backend
if curl -s --max-time 3 "http://localhost:8484/api/health" > /dev/null 2>&1; then
    ok "Backend running on http://localhost:8484"
else
    warn "Backend not yet responding — check logs: $LOG_DIR/ucore-server-stderr.log"
fi

# Check menu
if pgrep -f "app.menu.unified_menu" > /dev/null 2>&1; then
    ok "Menu bar app running (look for 🍿 in menu bar)"
else
    warn "Menu bar app not running — check logs: $LOG_DIR/ucore-menu-stderr.log"
fi

# Check frontend
if curl -s --max-time 3 "http://localhost:5175" > /dev/null 2>&1; then
    ok "Frontend running on http://localhost:5175"
else
    warn "Frontend not yet responding — check logs: $LOG_DIR/ucore-frontend-stderr.log"
fi

# ─── Done ────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       uCore Setup Complete! 🎉           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Backend:  http://localhost:8484"
echo "  Frontend: http://localhost:5175"
echo "  Menu:     Look for 🍿 in the macOS menu bar"
echo ""
echo "  Logs:     $LOG_DIR"
echo "  Data:     $DATA_DIR"
echo ""
echo "  To uninstall: ./scripts/setup.sh --uninstall"
echo ""
