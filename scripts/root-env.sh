#!/bin/bash
# root-env.sh — Source this to get ROOT and all repo paths
# Usage: source ./scripts/root-env.sh
export ROOT="${ROOT:-$HOME/Code}"

# Export per-repo paths
export UCORE_ROOT="$ROOT/uCore"
export UCODE_ROOT="$ROOT/uCode"
export UDOCS_ROOT="$ROOT/uDocs"
export UPALCE_ROOT="$ROOT/uPlace"
export DEVELOPER_ROOT="$ROOT/uCore"

# Verify spine
if [ -f "$ROOT/.udos-root" ]; then
  echo "✅ Spine locked: $ROOT"
else
  echo "⚠️  Run scripts/install-root.sh to lock the spine"
fi
