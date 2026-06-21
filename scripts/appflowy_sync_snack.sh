#!/usr/bin/env bash
set -euo pipefail

# AppFlowy Sync snack: export local AppFlowy sqlite snapshots to vault.
# Usage: ./scripts/appflowy_sync_snack.sh [vault_dir]

VAULT_DIR="${1:-$HOME/vault/@appflowy}"

curl -sS -X POST "http://127.0.0.1:8484/api/knowledge/local/export" \
  -H "Content-Type: application/json" \
  -d "{\"vault_dir\": \"${VAULT_DIR}\", \"limit_per_table\": 2000}" | cat

echo
