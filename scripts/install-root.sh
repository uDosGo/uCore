#!/bin/bash
# install-root.sh — Set UDOS_ROOT env var and lock the spine of all repos under ~/Code/
set -euo pipefail

UDOS_ROOT="${UDOS_ROOT:-${ROOT:-${UDOS_CODE:-$HOME/Code}}}"
echo "Setting UDOS_ROOT=$UDOS_ROOT"

ZSHRC="$HOME/.zshrc"
if ! grep -q 'export UDOS_ROOT=' "$ZSHRC" 2>/dev/null; then
  echo 'export UDOS_ROOT="$HOME/Code"' >> "$ZSHRC"
  echo "Added UDOS_ROOT to $ZSHRC"
else
  echo "UDOS_ROOT already in $ZSHRC"
fi

if ! grep -q 'export ROOT=' "$ZSHRC" 2>/dev/null; then
  echo 'export ROOT="$UDOS_ROOT"' >> "$ZSHRC"
fi

mkdir -p "$UDOS_ROOT"
touch "$UDOS_ROOT/.udos-root"
echo "Created $UDOS_ROOT/.udos-root"
echo "Spine locked: all repos under \$UDOS_ROOT are discoverable."
