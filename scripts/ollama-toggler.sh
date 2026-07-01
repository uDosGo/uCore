#!/bin/bash
# ollama-toggler.sh — Start/stop/status Ollama on-demand
set -euo pipefail

OLLAMA_PID=$(ps aux | grep -E "[o]llama serve" | awk '{print $2}')

case "${1:-}" in
start)
  if [ -n "$OLLAMA_PID" ]; then
    MEM=$(ps -o rss= -p "$OLLAMA_PID" 2>/dev/null | awk '{printf "%.0f", $1/1024}')
    echo "✅ Ollama already running (PID: $OLLAMA_PID, ~${MEM}MB)"
  else
    echo "🚀 Starting Ollama..."
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 2
    NEW_PID=$(pgrep -f 'ollama serve' 2>/dev/null || echo "?")
    echo "✅ Started (PID: $NEW_PID)"
  fi
  ;;
stop)
  if [ -n "$OLLAMA_PID" ]; then
    echo "⏹️  Stopping Ollama (PID: $OLLAMA_PID)..."
    kill -TERM "$OLLAMA_PID"
    sleep 1
    if ps -p "$OLLAMA_PID" > /dev/null 2>&1; then
      sleep 2
      kill -KILL "$OLLAMA_PID" 2>/dev/null || true
    fi
    pkill -f "ollama runner" 2>/dev/null || true
    echo "✅ Stopped"
  else
    echo "ℹ️  Ollama not running"
  fi
  ;;
status)
  if [ -n "$OLLAMA_PID" ]; then
    MEM=$(ps -o rss= -p "$OLLAMA_PID" 2>/dev/null | awk '{printf "%.1f", $1/1024}')
    echo "✅ Ollama running (PID: $OLLAMA_PID, RAM: ${MEM}MB)"
    echo ""
    ollama list 2>/dev/null || echo "(no models listed)"
    ACTIVE=$(lsof -i :11434 -sTCP:ESTABLISHED 2>/dev/null | wc -l | tr -d ' ')
    if [ "${ACTIVE:-0}" -gt 1 ]; then
      echo "🔌 $((ACTIVE - 1)) active connection(s)"
    else
      echo "💤 No active connections"
    fi
  else
    echo "❌ Ollama not running"
  fi
  ;;
*)
  echo "Usage: ollama-toggler {start|stop|status}"
  exit 1
  ;;
esac
