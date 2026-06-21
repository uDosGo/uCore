#!/bin/bash
# install-root.sh — Set ROOT env var and lock the spine of all repos under ~/Code/
set -euo pipefail

ROOT="${ROOT:-$HOME/Code}"
echo "Setting ROOT=$ROOT"

ZSHRC="$HOME/.zshrc"
if ! grep -q 'export ROOT=' "$ZSHRC" 2>/dev/null; then
  echo 'export ROOT="$HOME/Code"' >> "$ZSHRC"
  echo "Added ROOT to $ZSHRC"
else
  echo "ROOT already in $ZSHRC"
fi

mkdir -p "$ROOT"
touch "$ROOT/.udos-root"
echo "Created $ROOT/.udos-root"
echo "Spine locked: all repos under \$ROOT are discoverable."
