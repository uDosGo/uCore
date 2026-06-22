#!/usr/bin/env bash
set -euo pipefail

# Repair/rebuild Cline + Continue extension configs for uCore MCP.
# - Backs up existing configs
# - Rewrites Cline MCP settings to known-good baseline
# - Rewrites Continue config with env-var API keys and updated model defaults

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$HOME/.ucore/ai-config-backups/$STAMP"
mkdir -p "$BACKUP_DIR"

backup_if_exists() {
  local file="$1"
  if [[ -f "$file" ]]; then
    cp "$file" "$BACKUP_DIR/$(basename "$file")"
  fi
}

CLINE_DIR="$HOME/.cline"
CONTINUE_DIR="$HOME/.continue"
mkdir -p "$CLINE_DIR" "$CONTINUE_DIR"

backup_if_exists "$CLINE_DIR/mcp_settings.json"
backup_if_exists "$CONTINUE_DIR/config.yaml"
backup_if_exists "$HOME/Library/Application Support/Code/User/settings.json"

cat > "$CLINE_DIR/mcp_settings.json" <<'JSON'
{
  "mcpServers": {
    "uCore": {
      "command": "python3",
      "args": [
        "/Users/fredbook/.continue/mcp-udos.py"
      ],
      "description": "uCore MCP - skills, knowledge, and automation",
      "disabled": false,
      "alwaysAllow": [
        "skill_attach_context",
        "skill_route_task",
        "skill_tasker_sync",
        "skill_vault_sync",
        "skill_ask_vault",
        "knowledge_search",
        "knowledge_list_workspaces",
        "knowledge_list_documents"
      ]
    }
  }
}
JSON

cat > "$CONTINUE_DIR/config.yaml" <<'YAML'
name: Continue Configuration
version: 4.0.0
schema: v1
models:
  - name: OpenRouter Qwen 2.5 Coder 7B
    provider: openrouter
    model: qwen/qwen-2.5-coder-7b-instruct
    apiKey: ${OPENROUTER_API_KEY}
    roles:
      - chat
      - edit
      - apply
      - summarize
  - name: OpenRouter DeepSeek V3
    provider: openrouter
    model: deepseek/deepseek-chat-v3-0324
    apiKey: ${OPENROUTER_API_KEY}
    roles:
      - chat
      - edit
  - name: Local Qwen 2.5 Coder 7B Q4
    provider: ollama
    model: qwen2.5-coder:7b-instruct-q4_K_M
    roles:
      - chat
      - edit
      - apply
      - autocomplete
  - name: Local Qwen 2.5 Coder 1.5B
    provider: ollama
    model: qwen2.5-coder:1.5b-instruct
    roles:
      - chat
      - autocomplete
mcpServers:
  - name: uCore
    command: python3
    args:
      - /Users/fredbook/.continue/mcp-udos.py
    env:
      UCORE_URL: http://127.0.0.1:8484
context:
  - provider: docs
    params:
      paths:
        - ~/Vault/binder/
rules:
  - name: ucore-mcp
    rule: Prefer uCore MCP tools for skills, maintenance, workflow, and knowledge operations.
YAML

echo "Repair complete"
echo "Backup: $BACKUP_DIR"
