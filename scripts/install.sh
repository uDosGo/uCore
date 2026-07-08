#!/bin/bash
# install.sh — uCore Production Installer
# Clones the repo and runs setup for a fresh installation.
#
# Usage: ./scripts/install.sh [--help] [--uninstall] [--branch main]
#
# This script:
#   1. Clones uCore from GitHub (if not already present)
#   2. Runs setup.sh to configure everything
#   3. Starts all services
#   4. Verifies the installation

set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────
UCORE_REPO="https://github.com/uDosGo/uCore.git"
UCORE_DIR="${UCORE_DIR:-$HOME/Code/uCore}"
BRANCH="main"

# ─── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Help ────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--help" ]]; then
    cat <<EOF
uCore Installer — Production Installation

Usage: ./scripts/install.sh [OPTIONS]

Options:
  --help            Show this help message
  --uninstall       Remove uCore and all components
  --branch <name>   Git branch to clone (default: main)
  --dir <path>      Installation directory (default: ~/Code/uCore)

This script installs uCore for production use:
  - Clones from GitHub
  - Installs all dependencies
    - Syncs locked vendor modules
  - Configures macOS launchd agents for auto-start
  - Starts all services

Prerequisites (installed automatically by bootstrap.sh):
  - Homebrew
  - Python 3.12.x (3.12 recommended)
  - Node.js 22+
  - pnpm 9+
EOF
    exit 0
fi

# ─── Parse Arguments ─────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --uninstall)
            if [[ -f "$UCORE_DIR/scripts/setup.sh" ]]; then
                bash "$UCORE_DIR/scripts/setup.sh" --uninstall
            else
                warn "uCore not found at $UCORE_DIR"
            fi
            exit 0
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --dir)
            UCORE_DIR="$2"
            shift 2
            ;;
        *)
            err "Unknown argument: $1"
            exit 2
            ;;
    esac
done

# ─── Banner ──────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║    uCore Installer — v4.0.0             ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ─── Prerequisites ───────────────────────────────────────────────────

info "Checking prerequisites..."

if ! command -v git &>/dev/null; then
    err "git is required. Install with: brew install git"
    exit 1
fi
ok "git: $(git --version 2>&1)"

if ! command -v python3 &>/dev/null; then
    err "Python 3 is required. Run bootstrap.sh first."
    exit 1
fi
ok "Python: $(python3 --version 2>&1)"

if ! command -v node &>/dev/null; then
    err "Node.js is required. Run bootstrap.sh first."
    exit 1
fi
ok "Node.js: $(node --version 2>&1)"

if ! command -v pnpm &>/dev/null; then
    err "pnpm is required. Run bootstrap.sh first."
    exit 1
fi
ok "pnpm: $(pnpm --version 2>&1)"

# ─── Clone Repository ────────────────────────────────────────────────

if [[ -d "$UCORE_DIR" ]]; then
    info "uCore already exists at $UCORE_DIR"
    info "Pulling latest changes..."
    cd "$UCORE_DIR"
    git fetch origin "$BRANCH" 2>&1 | tail -1
    git reset --hard "origin/$BRANCH" 2>&1 | tail -1
    ok "Updated to latest $BRANCH"
else
    info "Cloning uCore from $UCORE_REPO (branch: $BRANCH)..."
    mkdir -p "$(dirname "$UCORE_DIR")"
    git clone --branch "$BRANCH" --depth 1 "$UCORE_REPO" "$UCORE_DIR"
    ok "Cloned to $UCORE_DIR"
fi

# ─── Run Setup ───────────────────────────────────────────────────────

info "Running setup..."
bash "$UCORE_DIR/scripts/setup.sh"

# ─── Verify ──────────────────────────────────────────────────────────

echo ""
info "Running final verification..."
sleep 3

ALL_OK=true

if curl -s --max-time 3 "http://localhost:8484/api/health" > /dev/null 2>&1; then
    ok "✅ Backend: http://localhost:8484"
else
    warn "⚠️  Backend not responding"
    ALL_OK=false
fi

if pgrep -f "app.menu.unified_menu" > /dev/null 2>&1; then
    ok "✅ Menu bar: 🍿 icon in menu bar"
else
    warn "⚠️  Menu bar app not running"
    ALL_OK=false
fi

if curl -s --max-time 3 "http://localhost:5175" > /dev/null 2>&1; then
    ok "✅ Frontend: http://localhost:5175"
else
    warn "⚠️  Frontend not responding"
    ALL_OK=false
fi

# ─── Done ────────────────────────────────────────────────────────────

echo ""
if [[ "$ALL_OK" == "true" ]]; then
    echo "╔══════════════════════════════════════════╗"
    echo "║   uCore Installation Complete! 🎉       ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""
    echo "  All services are running."
    echo "  Look for 🍿 in the macOS menu bar."
    echo ""
    echo "  To uninstall: $UCORE_DIR/scripts/install.sh --uninstall"
else
    echo "╔══════════════════════════════════════════╗"
    echo "║   Installation completed with warnings  ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""
    echo "  Some services may still be starting."
    echo "  Check logs: ~/.ucore/logs/"
    echo ""
    echo "  To retry: $UCORE_DIR/scripts/setup.sh"
fi
echo ""
