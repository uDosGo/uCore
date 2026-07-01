#!/bin/bash
# install_ucore_menu_launchd.sh - Install uCore Menu bar app launchd agent
# Usage: ./scripts/install_ucore_menu_launchd.sh [--uninstall] [--uninstall-all]

set -euo pipefail

UCORE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$UCORE_ROOT/backend"
LABEL="com.udos.ucore-menu"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="$HOME/.ucore/logs"

usage() {
    cat <<EOF
Usage:
  scripts/install_ucore_menu_launchd.sh           Install uCore Menu launchd agent
  scripts/install_ucore_menu_launchd.sh --uninstall Remove uCore Menu launchd agent
  scripts/install_ucore_menu_launchd.sh --uninstall-all Remove all uCore launchd agents

Installs a launchd agent that runs the uCore menu bar app at login.
EOF
}

UNINSTALL=0
UNINSTALL_ALL=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --uninstall)
            UNINSTALL=1
            shift
            ;;
        --uninstall-all)
            UNINSTALL_ALL=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            usage
            exit 2
            ;;
    esac
done

# Uninstall all uCore agents
if [[ "$UNINSTALL_ALL" -eq 1 ]]; then
    echo "🧹 Removing all uCore launchd agents..."
    launchctl unload "$HOME/Library/LaunchAgents/com.udos.ucore-menu.plist" 2>/dev/null || true
    launchctl unload "$HOME/Library/LaunchAgents/com.udos.ucore-server.plist" 2>/dev/null || true
    rm -f "$HOME/Library/LaunchAgents/com.udos.ucore-menu.plist"
    rm -f "$HOME/Library/LaunchAgents/com.udos.ucore-server.plist"
    echo "✅ All uCore launchd agents removed"
    exit 0
fi

# Uninstall just the menu agent
if [[ "$UNINSTALL" -eq 1 ]]; then
    echo "🧹 Removing uCore Menu launchd agent..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm -f "$PLIST_PATH"
    echo "✅ uCore Menu launchd agent removed"
    exit 0
fi

# Determine Python binary
if [[ -f "$BACKEND_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
else
    PYTHON_BIN="/usr/bin/python3"
fi

# Ensure directories exist
mkdir -p "$(dirname "$PLIST_PATH")"
mkdir -p "$LOG_DIR"

# Create plist
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON_BIN}</string>
    <string>-m</string>
    <string>app.menu.unified_menu</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${BACKEND_DIR}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/ucore-menu-stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/ucore-menu-stderr.log</string>
  <key>TimeOut</key>
  <integer>60</integer>
  <key>EnvironmentVariables</key>
  <dict>
    <key>UCORE_DEBUG</key>
    <string>1</string>
  </dict>
</dict>
</plist>
EOF

# Unload existing (if any) and load new
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "✅ Installed uCore Menu launchd agent"
echo "   Label: ${LABEL}"
echo "   Plist: ${PLIST_PATH}"
echo "   Python: ${PYTHON_BIN}"
echo ""
echo "The uCore menu will now start automatically at login."
echo "To uninstall: $0 --uninstall"