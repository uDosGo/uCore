<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Skills</h3>
      <UBadge type="success">{{ loading ? '...' : skills.length + ' installed' }}</UBadge>
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
import { ref, onMounted } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

interface Skill {
  id: string
  name: string
  icon: string
  active: boolean
  version: string
  runs: number
  description: string
}

const skills = ref<Skill[]>([])
const loading = ref(true)

const iconMap: Record<string, string> = {
  'vault-sync': 'sync',
  'tasker': 'task',
  'git-maintenance': 'build',
  'usx-standard': 'palette',
  'daily-backup': 'backup',
  'brain-sync': 'psychology',
  'dev-destroy-rebuild': 'restart_alt',
  'docs-roundup': 'description',
  'tasker-ingest': 'input',
  'ask-vault': 'search',
  'file-edit-enhancer': 'edit',
}

async function fetchSkills() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/skills`, {
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) {
      const data = await res.json()
      const list = data.skills || data || []
      skills.value = list.map((s: any) => ({
        id: s.skill_id || s.id || s.name?.toLowerCase() || 'unknown',
        name: s.name || s.skill_id || 'Unknown Skill',
        icon: iconMap[s.skill_id] || iconMap[s.id] || 'extension',
        active: s.active !== false,
        version: s.version || '1.0',
        runs: s.runs || s.run_count || 0,
        description: s.description || s.skill_id || '',
      }))
    }
  } catch {
    // Fallback
    skills.value = [
      { id: 'backend-offline', name: 'Skills Unavailable', icon: 'error', active: false, version: '—', runs: 0, description: 'Skills backend unreachable. Start the uCore server.' },
    ]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSkills()
})
</script>

<style scoped>
.developer-panel { max-width: calc(var(--usx-spacing-2xl) * 25); }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }
.developer-card-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); background: var(--usx-color-background); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-semibold); flex: 1; }
.developer-card-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin: 0 0 var(--usx-spacing-xs); }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
</style>
