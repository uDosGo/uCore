#!/bin/bash
# appflowy_sync.sh – Sync local vault to AppFlowy workspace (self-hosted)
# Usage: ./scripts/appflowy_sync.sh [binder_name]

set -euo pipefail

# Configuration
BINDER_NAME="${1:-vault_sync}"
SPOOL_PATH="${UCORE_SNACKS_REPLIES:-$HOME/.local/share/snackmachine/replies.jsonl}"
SYNC_CONFIG="${UCORE_SYNC_CONFIG:-$HOME/.ucore/sync_config.yaml}"

# Ensure spool directory exists
mkdir -p "$(dirname "$SPOOL_PATH")"

# Logging function
log_to_spool() {
    local status="$1"
    local output="$2"
    echo "{\"snack_id\":\"appflowy_sync\",\"status\":\"${status}\",\"output\":\"${output}\",\"binder\":\"${BINDER_NAME}\",\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" >> "$SPOOL_PATH"
}

# Step 1: Run the Python sync module
echo "📦 Syncing vault to AppFlowy workspace..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../backend"

if [[ ! -d "$BACKEND_DIR" ]]; then
    echo "❌ Backend directory not found: $BACKEND_DIR"
    log_to_spool "error" "Backend directory not found"
    exit 1
fi

# Run sync using Python module
RESULT=$(cd "$BACKEND_DIR" && .venv/bin/python scripts/appflowy_import_workspaces.py --config "$SYNC_CONFIG" --source "$BINDER_NAME" 2>&1)
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ Sync completed successfully!"
    log_to_spool "success" "Workspace '$BINDER_NAME' synced"
    echo "$RESULT"
else
    echo "❌ Sync failed. Error: $RESULT"
    log_to_spool "error" "Sync failed: $RESULT"
    exit 1
fi

echo "Done."