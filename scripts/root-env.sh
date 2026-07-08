#!/bin/bash
# root-env.sh — Source this to get UDOS_ROOT and all repo paths
# Usage: source ./scripts/root-env.sh
export UDOS_ROOT="${UDOS_ROOT:-${ROOT:-${UDOS_CODE:-$HOME/Code}}}"
export ROOT="$UDOS_ROOT"

# Export per-repo paths
export UCORE_ROOT="$UDOS_ROOT/uCore"
export UCODE_ROOT="$UDOS_ROOT/uCode"
export UDOCS_ROOT="$UDOS_ROOT/uDocs"
export UPLACE_ROOT="$UDOS_ROOT/uPlace"
# Backward compatibility for legacy typo in older shell configs/scripts.
export UPALCE_ROOT="${UPALCE_ROOT:-$UPLACE_ROOT}"
export DEVELOPER_ROOT="$UDOS_ROOT/uCore"

# Verify spine
if [ -f "$UDOS_ROOT/.udos-root" ]; then
  echo "✅ Spine locked: $UDOS_ROOT"
else
  echo "⚠️  Run scripts/install-root.sh to lock the spine"
fi
