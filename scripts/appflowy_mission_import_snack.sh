#!/usr/bin/env bash
set -euo pipefail

# AppFlowy Mission Import snack: read task-like rows and print/import candidates.
# Usage: ./scripts/appflowy_mission_import_snack.sh [db-key]

DB_KEY="${1:-database}"
SQL="SELECT * FROM row_table LIMIT 50"

curl -sS -X POST "http://127.0.0.1:8484/api/knowledge/local/query" \
  -H "Content-Type: application/json" \
  -d "{\"db\": \"${DB_KEY}\", \"sql\": \"${SQL}\", \"write\": false}" | cat

echo
