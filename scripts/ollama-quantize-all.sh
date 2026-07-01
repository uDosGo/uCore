#!/bin/bash
# ollama-quantize-all.sh — Check for Q4_K_M versions and suggest conversion
set -euo pipefail

echo "=== Model Quantization Check ==="
ollama list 2>/dev/null | grep -v NAME | while read -r name _ size rest; do
  model_name="${name%%:*}"
  model_tag="${name#*:}"
  if [[ "$model_tag" != *"q4"* ]] && [[ "$model_tag" != *"q8"* ]]; then
    echo "📦 $name (${size}) → checking for Q4_K_M..."
    Q4_NAME="${model_name}:${model_tag}-q4_K_M"
    # Check if it exists by trying to pull (metadata only)
    if curl -sf "http://localhost:11434/api/tags" 2>/dev/null | grep -q "${Q4_NAME}"; then
      echo "   ✅ Q4_K_M available: ${Q4_NAME}"
    else
      echo "   ⚠️  No Q4_K_M version found (may be available upstream)"
    fi
  else
    echo "✅ $name — already quantized"
  fi
done
