#!/bin/bash
# uCode Recovery System - Pre-Reset Backup Script
# Creates backup of all dev configurations before reset

set -e

BACKUP_DIR=~/.ucode/backup/$(date +%Y-%m-%d_%H-%M-%S)
mkdir -p $BACKUP_DIR

echo "📦 Creating pre-reset backup to: $BACKUP_DIR"

# 1. Backup critical configs
cp -r ~/.ucode/config $BACKUP_DIR/ 2>/dev/null || true
cp -r ~/.ucode/instructions $BACKUP_DIR/ 2>/dev/null || true
cp -r ~/.ucode/skills $BACKUP_DIR/ 2>/dev/null || true
cp -r ~/.ucode/tasks $BACKUP_DIR/ 2>/dev/null || true
cp -r ~/.ucode/mcp $BACKUP_DIR/ 2>/dev/null || true

# 2. Backup agent state
cp -r ~/.cline $BACKUP_DIR/.cline-backup 2>/dev/null || true
cp -r ~/.hivemind $BACKUP_DIR/.hivemind-backup 2>/dev/null || true

# 3. Backup secret store (encrypted)
cp ~/.ucode/.env $BACKUP_DIR/.env 2>/dev/null || true
cp ~/.ucode/secrets/store.json $BACKUP_DIR/secrets-store.json 2>/dev/null || true

# 4. Backup task history
cp ~/.ucode/tasks/history.db $BACKUP_DIR/tasks-history.db 2>/dev/null || true

# 5. Backup OpenRouter fallback config
cp ~/.ucode/config/openrouter-fallback.toml $BACKUP_DIR/openrouter-fallback.toml 2>/dev/null || true

# 6. Create state manifest
cat > $BACKUP_DIR/pre-reset-state.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "user": "$USER",
  "hostname": "$(hostname)",
  "components_backed_up": ["config", "instructions", "skills", "tasks", "mcp", "cline", "hivemind", "secrets"],
  "total_size_mb": $(du -sm $BACKUP_DIR 2>/dev/null | cut -f1 || echo "0"),
  "checksum": "$(find $BACKUP_DIR -type f -exec md5sum {} \; 2>/dev/null | sort | md5sum | cut -d' ' -f1 || echo "none")"
}
EOF

echo "✅ Backup complete: $BACKUP_DIR/pre-reset-state.json"