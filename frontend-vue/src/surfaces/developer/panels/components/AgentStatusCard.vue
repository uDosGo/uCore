<template>
  <div class="agent-status">
    <div class="agent-status__header">
      <span class="agent-status__title">Agent Status</span>
    </div>

    <div class="agent-status__grid">
      <!-- Hivemind -->
      <div class="agent-card">
        <div class="agent-card__icon"><UIcon name="smart_toy" /></div>
        <div class="agent-card__body">
          <span class="agent-card__name">Hivemind</span>
          <span class="agent-card__state" :class="hivemindOnline ? 'state--online' : 'state--offline'">
            {{ hivemindOnline ? (hivemindDetail || 'Running') : 'Offline' }}
          </span>
        </div>
      </div>

      <!-- Roundtable -->
      <div class="agent-card">
        <div class="agent-card__icon"><UIcon name="group" /></div>
        <div class="agent-card__body">
          <span class="agent-card__name">Roundtable</span>
          <span class="agent-card__state" :class="roundtableOnline ? 'state--online' : 'state--offline'">
            {{ roundtableOnline ? (roundtableDetail || 'Available') : 'Offline' }}
          </span>
        </div>
      </div>

      <!-- Cline -->
      <div class="agent-card">
        <div class="agent-card__icon"><UIcon name="bolt" /></div>
        <div class="agent-card__body">
          <span class="agent-card__name">Cline</span>
          <span class="agent-card__state" :class="clineActive ? 'state--online' : 'state--idle'">
            {{ clineActive ? 'Active' : 'Idle' }}
          </span>
        </div>
      </div>

      <!-- Ollama -->
      <div class="agent-card">
        <div class="agent-card__icon"><UIcon name="smart_toy" /></div>
        <div class="agent-card__body">
          <span class="agent-card__name">Ollama</span>
          <span class="agent-card__state" :class="ollamaOnline ? 'state--online' : 'state--offline'">
            {{ ollamaOnline ? ollamaModelCount + ' models' : 'Offline' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UIcon from '../../../../skills/atoms/UIcon.vue'

const props = defineProps<{
  agents: {
    hivemind?: { status?: string; detail?: string; data?: Record<string, unknown> }
    roundtable?: { status?: string; detail?: string }
    cline?: { active?: boolean; detail?: string }
    ollama?: { online?: boolean; model_count?: number; models?: Array<{ name: string }> }
  } | null
}>()

const hivemindOnline = computed(() =>
  props.agents?.hivemind?.status === 'running' || !!props.agents?.hivemind?.data,
)

const hivemindDetail = computed(() => props.agents?.hivemind?.detail || '')

const roundtableOnline = computed(() =>
  props.agents?.roundtable?.status !== 'unknown',
)

const roundtableDetail = computed(() => props.agents?.roundtable?.detail || '')

const clineActive = computed(() => props.agents?.cline?.active ?? false)

const ollamaOnline = computed(() => props.agents?.ollama?.online ?? false)

const ollamaModelCount = computed(() => props.agents?.ollama?.model_count ?? 0)
</script>

<style scoped>
.agent-status {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.agent-status__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.agent-status__title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.agent-status__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--usx-spacing-sm);
}

.agent-card {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.agent-card__icon {
  font-size: var(--usx-font-size-lg);
  flex-shrink: 0;
}

.agent-card__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.agent-card__name {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
}

.agent-card__state {
  font-size: var(--usx-font-size-xs);
}

.state--online { color: var(--usx-color-success); }
.state--offline { color: var(--usx-color-danger); }
.state--idle { color: var(--usx-color-on-surface-muted); }
</style>