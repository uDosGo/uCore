#!/bin/bash
# uCode Recovery System - OpenRouter Fallback Activation Script
# Switches to direct OpenRouter API access when Hivemind fails

echo "🔄 Switching to OpenRouter-only fallback mode..."

# 1. Validate OpenRouter API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ OPENROUTER_API_KEY not set in environment"
    echo "   Please set: export OPENROUTER_API_KEY=your_key"
    exit 1
fi

# 2. Load fallback config
mkdir -p ~/.ucode/config
cat > ~/.ucode/config/current-routing.toml << EOF
[metadata]
name = "openrouter-fallback"
version = "1.0.0"
description = "Direct OpenRouter API access - no Hivemind, no Roundtable"

[openrouter]
api_key = "\${OPENROUTER_API_KEY}"
base_url = "https://openrouter.ai/api/v1"
timeout = 120
max_retries = 3

[models]
default = "openai/gpt-oss-20b"
coding = "meta-llama/llama-3.3-70b-instruct"
reasoning = "deepseek/deepseek-v4-pro"
fallback = "nvidia/nemotron-3-super"

[routing]
strategy = "cost-first"
max_cost_per_request = 0.05
free_tier_first = true
provider_fallbacks = true

[features]
prompt_caching = true
reasoning_effort = "medium"
streaming = false
EOF

# 3. Disable Hivemind consensus
export HIVEMIND_ENABLED=false

# 4. Log the switch
mkdir -p ~/.ucode/logs
echo "✅ OpenRouter fallback activated at $(date -Iseconds)" >> ~/.ucode/logs/fallback-events.log

echo "✅ OpenRouter-only fallback mode active"
echo ""
echo "   🟢 Available models:"
echo "   - Default: openai/gpt-oss-20b (\$0.02/M)"
echo "   - Coding: meta-llama/llama-3.3-70b-instruct"
echo "   - Reasoning: deepseek/deepseek-v4-pro"
echo "   - Fallback: nvidia/nemotron-3-super (\$0.09/M)"
echo ""
echo "   🔄 To switch back to Hivemind mode:"
echo "   ucode dev enable --hivemind"