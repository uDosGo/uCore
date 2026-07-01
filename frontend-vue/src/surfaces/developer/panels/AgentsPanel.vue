<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Dev Agents</h3>
      <UBadge type="success">{{ agents.length }} active</UBadge>
    </div>
    <div class="developer-card-list">
      <div v-for="agent in agents" :key="agent.id" class="developer-card">
        <div class="developer-card-header">
          <UIcon :name="agent.icon" />
          <span class="developer-card-title">{{ agent.name }}</span>
          <UBadge :type="agent.active ? 'success' : 'info'" size="sm">
            {{ agent.active ? 'active' : 'idle' }}
          </UBadge>
        </div>
        <p class="developer-card-desc">{{ agent.description }}</p>
        <div class="developer-card-meta">
          <span>{{ agent.model }}</span>
          <span>{{ agent.tasks }} tasks</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component AgentsPanel
 * @description Dev agents management panel.
 * @category surfaces/developer
 */
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const agents = [
  { id: 'cline', name: 'Cline', icon: 'code', active: true, model: 'Claude Sonnet 4', tasks: 12, description: 'AI coding assistant for complex multi-step tasks' },
  { id: 'copilot', name: 'Copilot', icon: 'smart_toy', active: true, model: 'GPT-4o', tasks: 8, description: 'Code completion and chat assistant' },
  { id: 'codex', name: 'Codex', icon: 'terminal', active: false, model: 'GPT-4o', tasks: 3, description: 'Autonomous code execution agent' },
  { id: 'devagent', name: 'DevAgent', icon: 'engineering', active: true, model: 'DeepSeek V3', tasks: 5, description: 'Full-stack development workflow agent' },
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
