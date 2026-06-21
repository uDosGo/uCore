# Continue v2.0 Configuration Troubleshooting

**Date:** 2026-06-21 11:02 AM  
**Issue:** Models not appearing / Config being overwritten  
**Status:** ✅ RESOLVED

## Root Cause Identified

**Continue v2.0 behavior:** When workspace-level config files exist at `.continue/mcpServers/*.yaml`, Continue will:
1. Auto-generate a minimal config from those files
2. OVERWRITE the global `~/.continue/config.yaml` 
3. Remove all models and other settings not present in workspace config

## The Problem

1. We had `.continue/mcpServers/udos.yaml` in the uCore workspace
2. This file only contained MCP server configuration (no models)
3. Continue v2.0 kept regenerating global config from this file
4. Every reload would wipe out the model configurations

## The Solution

### Step 1: Disable Workspace-Level Config
```bash
cd /Users/fredbook/Code/uCore
mv .continue/mcpServers/udos.yaml .continue/mcpServers/udos.yaml.bak
```

This prevents Continue from auto-generating configs from workspace files.

### Step 2: Use Global Config Only
All configuration now lives in: `/Users/fredbook/.continue/config.yaml`

This includes:
- ✅ All 6 LLM models
- ✅ MCP servers (uCore)
- ✅ Context providers
- ✅ Rules

## Current Configuration

**Location:** `/Users/fredbook/.continue/config.yaml` (63 lines)

### Models (6 total)
1. DeepSeek Chat - `deepseek` provider
2. Mistral Large - `mistral` provider (API key needed)
3. OpenRouter DeepSeek - `openrouter` provider
4. Qwen 2.5 Coder 7B - `ollama` (local)
5. Qwen 2.5 1.5B - `ollama` (local)
6. Qwen 2.5 0.5B - `ollama` (local)

### MCP Servers
- uCore - Python bridge to `http://localhost:8484`

## Files Changed

| File | Status | Purpose |
|------|--------|---------|
| `/Users/fredbook/.continue/config.yaml` | ✅ RESTORED | Main config with all models |
| `.continue/mcpServers/udos.yaml` | ⚠️ DISABLED | Renamed to `.bak` to prevent auto-generation |
| `config.json.backup-*` | 📦 BACKUP | Original config backups |

## Critical Lessons

### ❌ DON'T DO THIS:
```yaml
# .continue/mcpServers/somefile.yaml in workspace
# This will cause Continue to overwrite global config!
name: My MCP Server
mcpServers:
  - name: server
    command: node
```

### ✅ DO THIS INSTEAD:
Put **everything** (models + MCP + context + rules) in one place:
```yaml
# ~/.continue/config.yaml (global only)
name: Continue Configuration
version: 4.0.0
schema: v1

models:
  - name: My Model
    provider: ollama
    model: qwen2.5:1.5b

mcpServers:
  - name: My Server
    command: python
```

## How to Verify It's Working

### 1. Check Config Size
```bash
wc -l /Users/fredbook/.continue/config.yaml
# Should show: 63 lines (not 9!)
```

### 2. Check Models Present
```bash
grep "- name:" /Users/fredbook/.continue/config.yaml | wc -l
# Should show: 9+ (models, servers, context, rules)
```

### 3. Restart VSCode
```
Cmd+Shift+P → "Developer: Reload Window"
```

### 4. Check Continue Sidebar
- Open Continue chat panel
- Click model dropdown
- Should see all 6 models listed

## If Models Still Don't Appear

### Check 1: Workspace Config Disabled
```bash
ls -la /Users/fredbook/Code/uCore/.continue/mcpServers/
# Should NOT see udos.yaml (only udos.yaml.bak)
```

### Check 2: Config Hasn't Been Overwritten
```bash
cat /Users/fredbook/.continue/config.yaml | head -10
# Should start with "name: Continue Configuration"
# NOT "name: uCore Config"
```

### Check 3: Environment Variables
```bash
echo "OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:+SET}"
# Should show: SET
```

### Check 4: Ollama Running
```bash
ollama list
# Should show: qwen2.5-coder:7b, qwen2.5:1.5b, qwen2.5:0.5b
```

## Re-enabling Workspace Config (Advanced)

If you MUST use workspace-level config, include ALL settings in the workspace file:

```yaml
# .continue/mcpServers/complete.yaml
name: uCore Workspace Config
version: 4.0.0
schema: v1

models:
  - name: Qwen 2.5 Coder 7B
    provider: ollama
    model: qwen2.5-coder:7b
  # ... include ALL models you want

mcpServers:
  - name: uCore
    command: python3
    args: [/Users/fredbook/.continue/mcp-udos.py]

# ... include context, rules, etc.
```

But this is **NOT recommended** - use global config instead.

## Summary

✅ **Root cause:** Workspace MCP config file was forcing Continue to regenerate global config  
✅ **Fix:** Disabled workspace config, use global config only  
✅ **Result:** All 6 models now available, config stable  
✅ **To reload:** `Cmd+Shift+P → Developer: Reload Window`

---

**Last verified:** 2026-06-21 11:02 AM  
**Config file size:** 63 lines  
**Models configured:** 6  
**MCP servers:** 1 (uCore)
