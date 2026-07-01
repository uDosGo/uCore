<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Skills</h3>
      <UBadge type="success">{{ skills.length }} installed</UBadge>
    </div>
    <div class="developer-card-list">
      <div v-for="skill in skills" :key="skill.id" class="developer-card">
        <div class="developer-card-header">
          <UIcon :name="skill.icon" />
          <span class="developer-card-title">{{ skill.name }}</span>
          <UBadge :type="skill.active ? 'success' : 'info'" size="sm">
            {{ skill.active ? 'active' : 'available' }}
          </UBadge>
        </div>
        <p class="developer-card-desc">{{ skill.description }}</p>
        <div class="developer-card-meta">
          <span>v{{ skill.version }}</span>
          <span>{{ skill.runs }} runs</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component SkillsPanel
 * @description Skills management panel — list, run, configure Skills.
 * @category surfaces/developer
 */
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const skills = [
  { id: 'vault-sync', name: 'Vault Sync', icon: 'sync', active: true, version: '2.1', runs: 48, description: 'Bidirectional markdown sync between AppFlowy and local vault' },
  { id: 'tasker-sync', name: 'Tasker Sync', icon: 'task', active: true, version: '1.3', runs: 22, description: 'Export AppFlowy workflow rows into Markdown task files' },
  { id: 'git-maintenance', name: 'Git Maintenance', icon: 'build', active: true, version: '1.0', runs: 15, description: 'Detect and repair uncommitted changes, orphaned branches' },
  { id: 'usx-standard', name: 'USX Standard', icon: 'palette', active: false, version: '2.0', runs: 8, description: 'Audit CSS for overrides/duplicates, repair to canonical standard' },
  { id: 'daily-backup', name: 'Daily Backup', icon: 'backup', active: true, version: '1.0', runs: 30, description: 'Scheduled daily backup of uCore data, config, and secrets' },
  { id: 'brain-sync', name: 'Brain Sync', icon: 'psychology', active: false, version: '1.0', runs: 5, description: 'Synthesize project changes into wisdom.md' },
]
</script>

<style scoped>
.developer-panel { max-width: 800px; }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: 600; margin: 0; }
.developer-card-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--pico-background-color, #30363d); border-radius: var(--usx-border-radius-lg); background: var(--pico-card-background-color, #161b22); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: 600; flex: 1; }
.developer-card-desc { font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); margin: 0 0 var(--usx-spacing-xs); }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--pico-muted-color, #8b949e); }
</style>
