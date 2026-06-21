#!/bin/bash
# ollama-idle-watchdog.sh — Auto-stop Ollama after idle timeout
set -euo pipefail

IDLE_THRESHOLD=15
LOG_FILE="${OLLAMA_LOG:-/tmp/ollama.log}"
OLLAMA_PID=$(ps aux | grep -E "[o]llama serve" | awk '{print $2}')

[ -z "$OLLAMA_PID" ] && exit 0

ACTIVE_CONNS=$(lsof -i :11434 -sTCP:ESTABLISHED 2>/dev/null | wc -l | tr -d ' ')
[ "${ACTIVE_CONNS:-0}" -gt 1 ] && exit 0

if [ -f "$LOG_FILE" ]; then
  LAST_MOD=$(stat -f %m "$LOG_FILE" 2>/dev/null || echo 0)
  NOW=$(date +%s)
  DIFF=$(( (NOW - LAST_MOD) / 60 ))
  if [ "$DIFF" -gt "$IDLE_THRESHOLD" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Idle ${DIFF}m — stopping Ollama" >> /tmp/ollama-watchdog.log
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    "$SCRIPT_DIR/ollama-toggler.sh" stop
  fi
fi
