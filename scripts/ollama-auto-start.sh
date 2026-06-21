#!/bin/bash
# ollama-auto-start.sh — Auto-start Ollama if needed before API calls
set -euo pipefail

if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
  exit 0
fi

echo "⚠️  Ollama not running — auto-starting..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/ollama-toggler.sh" ]; then
  "$SCRIPT_DIR/ollama-toggler.sh" start
else
  nohup ollama serve > /tmp/ollama.log 2>&1 &
  sleep 2
fi

for i in $(seq 1 10); do
  if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama ready"
    exit 0
  fi
  sleep 1
done
echo "⚠️  Ollama started but not yet ready"
