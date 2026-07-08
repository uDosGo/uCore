#!/bin/bash
# bootstrap.sh — First-Time macOS Bootstrap for uCore
#
# This script installs all prerequisites on a fresh macOS system:
#   1. Homebrew (if not installed)
#   2. Python 3.12 via Homebrew
#   3. Node.js 22 via Homebrew
#   4. pnpm via Homebrew
#   5. git (via Homebrew, if needed)
#   6. Clones uCore and runs install.sh
#
# Usage: curl -fsSL https://raw.githubusercontent.com/uDosGo/uCore/main/scripts/bootstrap.sh | bash
#    Or: ./scripts/bootstrap.sh [--help] [--branch main]

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
uCore Bootstrap — First-Time macOS Setup

Usage: curl -fsSL https://raw.githubusercontent.com/uDosGo/uCore/main/scripts/bootstrap.sh | bash
   Or: ./scripts/bootstrap.sh [OPTIONS]

Options:
  --help            Show this help message
  --branch <name>   Git branch to clone (default: main)
  --dir <path>      Installation directory (default: ~/Code/uCore)

This script installs all prerequisites on a fresh macOS system:
  1. Homebrew (package manager)
  2. Python 3.12
  3. Node.js 22
  4. pnpm
  5. git
  6. uCore (via install.sh)

Run this once on a new Mac, then uCore will auto-start on every login.
EOF
    exit 0
fi

# ─── Parse Arguments ─────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
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
echo "║    uCore Bootstrap — macOS Setup        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
info "This script will install prerequisites and set up uCore."
echo ""

# ─── 1. Homebrew ─────────────────────────────────────────────────────

info "Step 1/6: Checking Homebrew..."
if command -v brew &>/dev/null; then
    ok "Homebrew already installed: $(brew --version 2>&1 | head -1)"
else
    info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ -f /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    ok "Homebrew installed"
fi

# Ensure brew is in PATH
if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# ─── 2. Python ───────────────────────────────────────────────────────

info "Step 2/6: Checking Python..."
PYTHON_INSTALLED=false
for cmd in python3.12 python3.13 python3 python3.11; do
    if command -v "$cmd" &>/dev/null; then
        PY_VER=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PY_MAJOR=${PY_VER%%.*}
        PY_MINOR=${PY_VER#*.}
        if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 11 ]]; then
            ok "Python $PY_VER already installed: $(which "$cmd")"
            PYTHON_INSTALLED=true
            break
        fi
    fi
done

if [[ "$PYTHON_INSTALLED" == "false" ]]; then
    info "Installing Python 3.12 via Homebrew..."
    brew install python@3.12
    ok "Python 3.12 installed"
fi

# ─── 3. Node.js ──────────────────────────────────────────────────────

info "Step 3/6: Checking Node.js..."
if command -v node &>/dev/null; then
    NODE_VER=$(node --version 2>&1 | grep -oE '[0-9]+' | head -1)
    if [[ "$NODE_VER" -ge 22 ]]; then
        ok "Node.js $(node --version) already installed"
    else
        info "Upgrading Node.js to v22 via Homebrew..."
        brew install node@22
        brew link --overwrite node@22
        ok "Node.js 22 installed"
    fi
else
    info "Installing Node.js 22 via Homebrew..."
    brew install node@22
    brew link --overwrite node@22
    ok "Node.js 22 installed"
fi

# ─── 4. pnpm ─────────────────────────────────────────────────────────

info "Step 4/6: Checking pnpm..."
if command -v pnpm &>/dev/null; then
    PNPM_VER=$(pnpm --version 2>&1 | grep -oE '^[0-9]+' | head -1)
    if [[ "$PNPM_VER" -ge 9 ]]; then
        ok "pnpm $(pnpm --version) already installed"
    else
        info "Upgrading pnpm via Homebrew..."
        brew upgrade pnpm 2>/dev/null || brew install pnpm
        ok "pnpm upgraded"
    fi
else
    info "Installing pnpm via Homebrew..."
    brew install pnpm
    ok "pnpm installed"
fi

# ─── 5. git ──────────────────────────────────────────────────────────

info "Step 5/6: Checking git..."
if command -v git &>/dev/null; then
    ok "git already installed: $(git --version 2>&1)"
else
    info "Installing git via Homebrew..."
    brew install git
    ok "git installed"
fi

# ─── 6. uCore ────────────────────────────────────────────────────────

info "Step 6/6: Installing uCore..."

# Clone the install script and run it
if [[ -f "$UCORE_DIR/scripts/install.sh" ]]; then
    info "uCore already cloned, running install..."
    bash "$UCORE_DIR/scripts/install.sh" --branch "$BRANCH"
else
    # Clone first, then install
    info "Cloning uCore from $UCORE_REPO..."
    mkdir -p "$(dirname "$UCORE_DIR")"
    git clone --branch "$BRANCH" --depth 1 "$UCORE_REPO" "$UCORE_DIR"
    ok "Cloned to $UCORE_DIR"
    
    bash "$UCORE_DIR/scripts/install.sh" --branch "$BRANCH"
fi

# ─── Done ────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   uCore Bootstrap Complete! 🎉          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  ✅ Homebrew installed/updated"
echo "  ✅ Python 3.12 installed"
echo "  ✅ Node.js 22 installed"
echo "  ✅ pnpm installed"
echo "  ✅ git installed"
echo "  ✅ uCore installed and running"
echo "  ✅ Locked vendor modules synced"
echo ""
echo "  Look for 🍿 in the macOS menu bar."
echo "  uCore will auto-start on every login."
echo ""
echo "  To uninstall: $UCORE_DIR/scripts/install.sh --uninstall"
echo ""
