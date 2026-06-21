# AppFlowy Bidirectional Integration

Date: 2026-06-21
Status: Active integration blueprint

## Goal

Provide two-way sync and AI access across:
- uDocs code documentation
- User vault at /Users/fredbook/Vault
- Shared vault container
- Public vault container

Tracking checklist:
- docs/APPFLOWY_SNACKBAR_LOCAL_FIRST_CHECKLIST.md

## Architecture

1. Git-canonical docs
- /Users/fredbook/Code/uDocs is canonical for engineering documentation.

2. Vault containers
- /Users/fredbook/Vault for personal knowledge.
- /Users/fredbook/Vault/Shared for team-shared docs.
- /Users/fredbook/Vault/Public for externally safe/public content.

3. AppFlowy bridge
- uCore knowledge endpoints provide workspace and document discovery/search.
- AppFlowy MCP server (external) can provide direct create/update flows when configured.

4. Sync engine
- scripts/appflowy_vault_sync.py performs bidirectional markdown sync based on config/vault-sync.yaml.

## Setup

1. Create runtime config from template:

```bash
cd /Users/fredbook/Code/uCore
cp config/vault-sync.example.yaml config/vault-sync.yaml
```

2. Adjust paths in config/vault-sync.yaml to match your actual vault layout.

3. Run dry-run first:

```bash
cd /Users/fredbook/Code/uCore
python scripts/appflowy_vault_sync.py --config config/vault-sync.yaml --dry-run
```

4. Execute real sync:

```bash
python scripts/appflowy_vault_sync.py --config config/vault-sync.yaml
```

## Conflict Handling

When both sides changed since the last sync snapshot, no overwrite occurs.
Conflict copies are created with suffixes:
- .conflict-left.TIMESTAMP.md
- .conflict-right.TIMESTAMP.md

## Suggested Automation

Use launchd or cron to run every 15 minutes.

Example command:

```bash
cd /Users/fredbook/Code/uCore && \
python scripts/appflowy_vault_sync.py --config config/vault-sync.yaml --summary-only
```

## MCP Integration (Cline)

For direct AppFlowy operations in AI chat, configure MCP servers in Cline and keep Hive-Vault for uDocs.

Example fragment for `~/.cline/mcp_settings.json`:

```json
{
  "mcpServers": {
    "hive-vault": {
      "command": "uvx",
      "args": ["--upgrade", "hive-vault"],
      "env": {
        "VAULT_PATH": "/Users/fredbook/Code/uDocs"
      }
    },
    "appflowy": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/appflowy-mcp", "run", "appflowy-mcp"]
    }
  }
}
```

## Guardrails

1. Keep secrets out of Public container.
2. Keep ADRs and architecture docs canonical in uDocs.
3. Use Shared for team-wide operational runbooks and glossary.
4. Keep Personal container for drafts and private notes.

## Validation Checklist

1. Dry-run returns expected copy/noop/conflict actions.
2. Real run writes state to ~/.ucore/vault-sync-state.json.
3. uCore /api/knowledge/workspaces returns data.
4. MCP client can query uDocs and AppFlowy sources.
