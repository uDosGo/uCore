<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Models</h3>
      <UBadge type="info">{{ loading ? '...' : models.length + ' available' }}</UBadge>
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
import { ref, computed, onMounted } from 'vue'
import UInput from '../../../skills/atoms/UInput.vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

const filter = ref('')
const models = ref<Array<{
  id: string
  name: string
  provider: string
  status: string
  contextWindow: string
  size: string
  description: string
}>>([])
const loading = ref(true)
const ollamaError = ref<string | null>(null)

async function fetchModels() {
  loading.value = true
  try {
    // Fetch from Ollama directly
    const ollamaRes = await fetch('http://localhost:11434/api/tags', {
      signal: AbortSignal.timeout(5000),
    })
    if (ollamaRes.ok) {
      const data = await ollamaRes.json()
      const ollamaModels = (data.models || []).map((m: any) => ({
        id: m.name,
        name: m.name,
        provider: 'ollama',
        status: 'ready',
        contextWindow: '—',
        size: m.size ? `${(m.size / 1e9).toFixed(1)}GB` : '—',
        description: `Local model (${m.digest?.slice(0, 12) || 'unknown'})`,
      }))
      models.value = ollamaModels
    } else {
      ollamaError.value = `Ollama returned ${ollamaRes.status}`
    }
  } catch (e: any) {
    ollamaError.value = e.message || 'Ollama unreachable'
  }

  // Also fetch OpenRouter/catalog models from backend
  try {
    const catRes = await fetch(`${API_BASE}/api/models`, {
      signal: AbortSignal.timeout(5000),
    })
    if (catRes.ok) {
      const data = await catRes.json()
      const catalogModels = (data.models || data || []).map((m: any) => ({
        id: m.id || m.name,
        name: m.name || m.id,
        provider: m.provider || 'openrouter',
        status: 'ready',
        contextWindow: m.context_window || '—',
        size: m.size || '—',
        description: m.description || `Available via ${m.provider || 'OpenRouter'}`,
      }))
      // Merge, avoiding duplicates
      const existingIds = new Set(models.value.map(m => m.id))
      for (const m of catalogModels) {
        if (!existingIds.has(m.id)) {
          models.value.push(m)
          existingIds.add(m.id)
        }
      }
    }
  } catch {
    // Catalog not available — that's fine, show Ollama models only
  }

  // If we still have nothing, show fallback
  if (models.value.length === 0) {
    models.value = [
      { id: 'fallback', name: 'No models found', provider: '—', status: 'offline', contextWindow: '—', size: '—', description: ollamaError.value || 'Connect Ollama or configure OpenRouter' },
    ]
  }

  loading.value = false
}

const filteredModels = computed(() => {
  if (!filter.value) return models.value
  const q = filter.value.toLowerCase()
  return models.value.filter(m => m.name.toLowerCase().includes(q) || m.provider.toLowerCase().includes(q))
})

onMounted(() => {
  fetchModels()
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
