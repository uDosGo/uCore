#!/usr/bin/env bash
set -euo pipefail

# Reset Cline config with backups. Default mode preserves API secrets.
# Use --full to also archive and clear secrets.

FULL_RESET="false"
if [[ "${1:-}" == "--full" ]]; then
  FULL_RESET="true"
fi

CLINE_DIR="$HOME/.cline"
DATA_DIR="$CLINE_DIR/data"
BACKUP_ROOT="$CLINE_DIR/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"

mkdir -p "$BACKUP_DIR"
mkdir -p "$DATA_DIR"

backup_if_exists() {
  local src="$1"
  if [[ -f "$src" ]]; then
    cp "$src" "$BACKUP_DIR/$(basename "$src")"
  fi
}

backup_if_exists "$CLINE_DIR/mcp_settings.json"
backup_if_exists "$DATA_DIR/globalState.json"
if [[ "$FULL_RESET" == "true" ]]; then
  backup_if_exists "$DATA_DIR/secrets.json"
fi

rm -f "$DATA_DIR/globalState.json"
if [[ "$FULL_RESET" == "true" ]]; then
  rm -f "$DATA_DIR/secrets.json"
fi

cat > "$CLINE_DIR/mcp_settings.json" <<'JSON'
{
  "mcpServers": {
    "uCore": {
      "command": "python3",
      "args": [
        "$HOME/.continue/mcp-udos.py"
      ],
      "description": "uCore MCP - skills, knowledge, and automation",
      "disabled": false,
      "alwaysAllow": [
        "skill_ask_vault",
        "skill_route_task",
        "skill_attach_context",
        "knowledge_search",
        "knowledge_list_workspaces",
        "knowledge_list_documents"
      ]
    }
  }
}
JSON

if [[ ! -f "$HOME/.continue/mcp-udos.py" ]]; then
  echo "WARN: MCP bridge missing at $HOME/.continue/mcp-udos.py"
fi

echo "Cline reset complete"
echo "Backup: $BACKUP_DIR"
echo "Full reset: $FULL_RESET"
