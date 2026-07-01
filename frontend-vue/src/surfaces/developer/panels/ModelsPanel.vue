<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Models</h3>
      <UBadge type="info">{{ models.length }} available</UBadge>
    </div>
    <UInput v-model="filter" placeholder="Filter models..." icon="search" class="developer-panel-search" />
    <div class="developer-card-list">
      <div v-for="model in filteredModels" :key="model.id" class="developer-card">
        <div class="developer-card-header">
          <UIcon name="smart_toy" />
          <span class="developer-card-title">{{ model.name }}</span>
          <UBadge :type="model.status === 'ready' ? 'success' : 'warning'" size="sm">
            {{ model.status }}
          </UBadge>
        </div>
        <div class="developer-card-meta">
          <span>{{ model.provider }}</span>
          <span>{{ model.contextWindow }} ctx</span>
          <span>{{ model.size }}</span>
        </div>
        <p class="developer-card-desc">{{ model.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component ModelsPanel
 * @description Model management panel — list, filter, and select LLM models.
 * @category surfaces/developer
 */
import { ref, computed } from 'vue'
import UInput from '../../../skills/atoms/UInput.vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const filter = ref('')

const models = ref([
  { id: 'llama3.2', name: 'Llama 3.2', provider: 'ollama', status: 'ready', contextWindow: '128K', size: '3B', description: 'Fast local model for coding and general tasks' },
  { id: 'mistral', name: 'Mistral 7B', provider: 'ollama', status: 'ready', contextWindow: '32K', size: '7B', description: 'Balanced performance for reasoning and code' },
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'openrouter', status: 'ready', contextWindow: '128K', size: '???', description: 'Premium model for complex analysis and generation' },
  { id: 'deepseek-v3', name: 'DeepSeek V3', provider: 'openrouter', status: 'ready', contextWindow: '64K', size: '671B MoE', description: 'High-performance open model for code and reasoning' },
  { id: 'claude-sonnet-4', name: 'Claude Sonnet 4', provider: 'openrouter', status: 'ready', contextWindow: '200K', size: '???', description: 'Anthropic\'s balanced model for agentic workflows' },
])

const filteredModels = computed(() => {
  if (!filter.value) return models.value
  const q = filter.value.toLowerCase()
  return models.value.filter(m => m.name.toLowerCase().includes(q) || m.provider.toLowerCase().includes(q))
})
</script>

<style scoped>
.developer-panel {
  max-width: 800px;
}

.developer-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--usx-spacing-md);
}

.developer-panel-title {
  font-size: var(--usx-font-size-lg);
  font-weight: 600;
  margin: 0;
}

.developer-panel-search {
  margin-bottom: var(--usx-spacing-md);
}

.developer-card-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.developer-card {
  padding: var(--usx-spacing-md);
  background: var(--pico-background-color, #30363d);
  border-radius: var(--usx-border-radius-lg);
  background: var(--pico-card-background-color, #161b22);
  transition: border-color 0.15s ease;
}

.developer-card:hover {
  border-color: var(--pico-primary, #58a6ff);
}

.developer-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-xs);
}

.developer-card-title {
  font-size: var(--usx-font-size-base);
  font-weight: 600;
  flex: 1;
}

.developer-card-meta {
  display: flex;
  gap: var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color, #8b949e);
  margin-bottom: var(--usx-spacing-xs);
}

.developer-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color, #8b949e);
  margin: 0;
}
</style>
