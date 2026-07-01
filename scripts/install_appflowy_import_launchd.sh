#!/usr/bin/env bash
set -euo pipefail

LABEL="com.udos.ucore.appflowy-import"
INTERVAL_SECONDS=1800
CONFIG_PATH="$HOME/.ucore/sync_config.yaml"
LOG_PATH="$HOME/.ucore/logs/appflowy-import.log"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
UCORE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
  cat <<EOF
Usage:
  scripts/install_appflowy_import_launchd.sh [--interval-seconds N] [--config PATH]
  scripts/install_appflowy_import_launchd.sh --uninstall

Installs a launchd agent that runs:
  python3 scripts/appflowy_import_workspaces.py --config <PATH>
EOF
}

UNINSTALL=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --interval-seconds)
      INTERVAL_SECONDS="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --uninstall)
      UNINSTALL=1
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

if [[ "$UNINSTALL" -eq 1 ]]; then
  launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
  rm -f "$PLIST_PATH"
  echo "Removed launchd job: $LABEL"
  exit 0
fi

mkdir -p "$(dirname "$PLIST_PATH")"
mkdir -p "$(dirname "$LOG_PATH")"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>-lc</string>
    <string>cd ${UCORE_DIR} && python3 scripts/appflowy_import_workspaces.py --config ${CONFIG_PATH} >> ${LOG_PATH} 2>&1</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>${INTERVAL_SECONDS}</integer>
  <key>StandardOutPath</key>
  <string>${LOG_PATH}</string>
  <key>StandardErrorPath</key>
  <string>${LOG_PATH}</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load "$PLIST_PATH"

echo "Installed launchd job: $LABEL"
echo "plist: $PLIST_PATH"
echo "config: $CONFIG_PATH"
echo "interval_seconds: $INTERVAL_SECONDS"
echo "log: $LOG_PATH"
