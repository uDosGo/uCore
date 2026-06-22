#!/usr/bin/env bash
set -euo pipefail

# One-shot repair + maintenance check for Cline/Continue + uCore MCP/API.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$SCRIPT_DIR/repair_ai_extensions_stack.sh"
bash "$SCRIPT_DIR/ai_stack_health_check.sh"

echo "AI stack rebuild and verification complete"
