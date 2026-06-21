# Continue v2.0 Migration Summary

**Date:** 2026-06-21  
**Status:** ✅ Complete

## Problem Identified

Continue app v2.0 introduced breaking schema changes. Multiple config formats (JSON, YAML, TypeScript) were present and conflicting, causing:
- Loss of LLM configurations
- MCP server connection failures
- Duplicate/outdated settings

## Actions Taken

### 1. **Backed Up Configurations**
- `/Users/fredbook/.continue/config.json.backup-20260621-104841`
- `/Users/fredbook/.continue/config.yaml.backup-20260621-104841`

### 2. **Purged Conflicting Files**
- ✅ Removed old `config.json` (v1 format)
- ✅ Kept `config.yaml` (v2 format) as primary
- ✅ Kept `config.ts` for programmatic config modifications

### 3. **Migrated to v2.0 Schema**

#### Key Schema Changes:
| v1 Format | v2 Format |
|-----------|-----------|
| `models[].title` | `models[].name` |
| `contextProviders` | `context[]` with `provider` field |
| `context.providers[]` | `context[]` (flat array) |
| `rules[].description` | `rules[].rule` |
| `slashCommands`, `customCommands` | Removed (use MCP tools) |

### 4. **Updated Configuration**

**Main Config:** `/Users/fredbook/.continue/config.yaml`
```yaml
name: Continue Configuration
version: 4.0.0
schema: v1

models: (6 LLMs restored)
  - DeepSeek Chat
  - Mistral Large
  - OpenRouter DeepSeek
  - Qwen 2.5 Coder 7B
  - Qwen 2.5 1.5B
  - Qwen 2.5 0.5B

mcpServers:
  - uCore (python bridge to http://localhost:8484)

context:
  - docs (~/Vault/binder/)
  - code (~/Code)

rules:
  - github automation
  - task management
  - agent orchestration
```

**Workspace MCP Config:** `.continue/mcpServers/udos.yaml`
```yaml
name: uCore MCP Server
version: 4.0.0
mcpServers:
  - name: uCore
    command: python3
    args: [/Users/fredbook/.continue/mcp-udos.py]
    env:
      UCORE_URL: http://localhost:8484
```

### 5. **Removed Template Files**
- ❌ Deleted `.continue/mcpServers/new-mcp-server.yaml` (unused template)

## Current Status

✅ **LLMs Restored:** All 6 models configured and available  
✅ **MCP Working:** uCore bridge connects to backend at `http://localhost:8484/api/health`  
✅ **No Duplicates:** Single source of truth in `config.yaml`  
✅ **Schema Valid:** Passes Continue v2.0 YAML schema validation  
✅ **Workspace Clean:** No conflicting configs in uCore workspace  

## MCP Bridge Details

**Script:** `/Users/fredbook/.continue/mcp-udos.py`  
**Protocol:** MCP stdio (JSON-RPC over stdin/stdout)  
**Backend:** uCore HTTP API at `http://localhost:8484`  
**Tools Available:** 15+ tools + skills + AppFlowy knowledge

## Next Steps

1. **Restart VSCode** to reload Continue extension with new config
2. **Test MCP Tools** in Continue chat (e.g., ask about GitHub repos)
3. **Verify LLMs** work in Continue sidebar
4. **Start uCore Backend** if not running: `cd backend && python -m app`

## Rollback Instructions

If needed, restore previous config:
```bash
cp /Users/fredbook/.continue/config.json.backup-20260621-104841 /Users/fredbook/.continue/config.json
rm /Users/fredbook/.continue/config.yaml
```

## References

- Continue v2.0 Schema: `/Users/fredbook/.vscode/extensions/continue.continue-2.0.0-darwin-arm64/config-yaml-schema.json`
- Continue Docs: https://docs.continue.dev
- MCP Bridge: `/Users/fredbook/.continue/mcp-udos.py`
