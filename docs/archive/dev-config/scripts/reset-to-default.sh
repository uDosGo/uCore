#!/bin/bash
# uCode Recovery System - Reset to Default Template Script
# Resets ALL Developer Mode configurations while preserving secrets

set -e

echo "⚠️  WARNING: This will reset ALL Developer Mode configurations"
echo "   - Developer Surface settings"
echo "   - VS Code & Cline extension state"
echo "   - Agent instructions and skills"
echo "   - Tasker lists"
echo "   - MCP connections"
echo "   - Hivemind configuration"
echo ""
echo "   ✅ PRESERVED:"
echo "   - API keys and secrets"
echo "   - OpenRouter fallback configuration"
echo "   - Task history"
echo "   - User vaults"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Aborted."
    exit 1
fi

# 1. Run pre-backup
if [ -f ~/.ucode/scripts/backup-pre-reset.sh ]; then
    ~/.ucode/scripts/backup-pre-reset.sh
fi

# 2. Destroy Developer Surface settings
echo "🔄 Resetting Developer Surface..."
rm -rf ~/.ucode/config/surface-settings.json 2>/dev/null || true
rm -rf ~/.ucode/config/workspaces.json 2>/dev/null || true
rm -rf ~/.ucode/config/tabs.json 2>/dev/null || true
rm -rf ~/.ucode/config/notifications.json 2>/dev/null || true
rm -rf ~/.ucode/cache/surface-session.json 2>/dev/null || true

# 3. Destroy VS Code extension state
echo "🔄 Resetting VS Code extensions..."
rm -rf ~/Library/Application\ Support/Code/User/globalStorage/saoudrizwan.claude-dev/ 2>/dev/null || true
rm -rf ~/Library/Application\ Support/Code/User/globalStorage/github.copilot-chat/cache/ 2>/dev/null || true

# 4. Destroy Cline config
echo "🔄 Resetting Cline..."
rm -rf ~/.cline/config.toml 2>/dev/null || true
rm -rf ~/.cline/kanban.db 2>/dev/null || true
rm -rf ./.cline/config.toml 2>/dev/null || true

# 5. Destroy agent instructions & skills
echo "🔄 Resetting agent instructions..."
rm -rf ~/.ucode/instructions/* 2>/dev/null || true
rm -rf ~/.ucode/skills/* 2>/dev/null || true

# 6. Destroy tasker lists
echo "🔄 Resetting tasker lists..."
rm -rf ~/.ucode/tasks/current.json 2>/dev/null || true
rm -rf ~/.ucode/tasks/schedule.json 2>/dev/null || true

# 7. Destroy MCP connections
echo "🔄 Resetting MCP connections..."
rm -rf ~/.ucode/mcp/servers.json 2>/dev/null || true
rm -rf ~/.ucode/mcp/configs/* 2>/dev/null || true
rm -rf ~/.ucode/config/agent-router.toml 2>/dev/null || true

# 8. Destroy Hivemind configuration
echo "🔄 Resetting Hivemind..."
rm -rf ~/.hivemind/config.toml 2>/dev/null || true
rm -rf ~/.hivemind/events.db 2>/dev/null || true
rm -rf ~/.hivemind/skills/cache/* 2>/dev/null || true
rm -rf ~/.hivemind/workspaces/* 2>/dev/null || true

# 9. Rebuild from template (if exists)
echo "🔄 Rebuilding from template..."
if [ -d ~/.ucode/templates/default ]; then
    cp -r ~/.ucode/templates/default/config/* ~/.ucode/config/ 2>/dev/null || true
    cp -r ~/.ucode/templates/default/instructions/* ~/.ucode/instructions/ 2>/dev/null || true
    cp -r ~/.ucode/templates/default/skills/* ~/.ucode/skills/ 2>/dev/null || true
    cp -r ~/.ucode/templates/default/tasks/* ~/.ucode/tasks/ 2>/dev/null || true
    cp -r ~/.ucode/templates/default/mcp/* ~/.ucode/mcp/ 2>/dev/null || true
fi

# 10. Restore fallback config
echo "🔄 Preserving OpenRouter fallback..."
if [ -f ~/.ucode/templates/default/config/openrouter-fallback.toml ]; then
    cp ~/.ucode/templates/default/config/openrouter-fallback.toml ~/.ucode/config/openrouter-fallback.toml 2>/dev/null || true
fi

# 11. Restore secrets (preserved)
if [ -f ~/.ucode/.env.backup ]; then
    cp ~/.ucode/.env.backup ~/.ucode/.env
fi

echo "✅ Reset complete!"
echo "   Template: default"
echo "   Backup: ~/.ucode/backup/$(date +%Y-%m-%d)"
echo ""
echo "🔄 To revert to OpenRouter fallback (if Hivemind fails):"
echo "   ucode dev fallback --openrouter-only"