<template>
  <div class="status-badges" v-if="statuses">
    <div
      v-for="badge in badges"
      :key="badge.id"
      class="status-badge"
      :class="{
        'status-badge--online': badge.online,
        'status-badge--offline': !badge.online,
      }"
      :title="badge.detail"
      @click="badge.onClick ? badge.onClick() : undefined"
      :style="{ cursor: badge.onClick ? 'pointer' : 'default' }"
    >
      <span class="status-badge__dot" :class="badge.online ? 'dot--online' : 'dot--offline'" />
      <span class="status-badge__label">{{ badge.label }}</span>
    </div>
  </div>
  <div v-else class="status-badges status-badges--loading">
    <span class="status-badges__loading">Loading statuses...</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface StatusBadgeData {
  id: string
  label: string
  online: boolean
  detail: string
  extra?: string
  onClick?: () => void
}

const props = defineProps<{
  statuses: Record<string, { online: boolean; detail: string; model_count?: number; activity_count?: number; template_count?: number; daily?: Record<string, number>; credits?: number }> | null
}>()

const emit = defineEmits<{
  (e: 'badge-click', id: string): void
}>()

const badges = computed<StatusBadgeData[]>(() => {
  if (!props.statuses) return []
  const s = props.statuses
  const budget = s.budget || {}
  const daily = (budget as any).daily || {}
  const used = daily.used || 0
  const limit = daily.limit || 0
  const remaining = limit - used

  return [
    {
      id: 'cline',
      label: 'Cline',
      online: s.cline?.online ?? false,
      detail: s.cline?.detail ?? '',
      onClick: () => emit('badge-click', 'cline'),
    },
    {
      id: 'openrouter',
      label: 'OpenRouter',
      online: s.openrouter?.online ?? false,
      detail: s.openrouter?.detail ?? '',
      extra: s.openrouter?.credits ? `$${(s.openrouter.credits as number).toFixed(2)}` : undefined,
      onClick: () => emit('badge-click', 'openrouter'),
    },
    {
      id: 'hivemind',
      label: 'Hivemind',
      online: s.hivemind?.online ?? false,
      detail: s.hivemind?.detail ?? '',
      onClick: () => emit('badge-click', 'hivemind'),
    },
    {
      id: 'roundtable',
      label: 'Roundtable',
      online: s.roundtable?.online ?? false,
      detail: s.roundtable?.detail ?? '',
      onClick: () => emit('badge-click', 'roundtable'),
    },
    {
      id: 'ollama',
      label: s.ollama?.online ? `Ollama (${s.ollama?.model_count ?? 0})` : 'Ollama',
      online: s.ollama?.online ?? false,
      detail: s.ollama?.detail ?? '',
      onClick: () => emit('badge-click', 'ollama'),
    },
    {
      id: 'feed',
      label: 'Feed Pod',
      online: s.feed?.online ?? false,
      detail: s.feed?.detail ?? '',
      onClick: () => emit('badge-click', 'feed'),
    },
    {
      id: 'slate',
      label: 'Slate',
      online: s.slate?.online ?? false,
      detail: s.slate?.detail ?? '',
      onClick: () => emit('badge-click', 'slate'),
    },
    {
      id: 'budget',
      label: `Budget: $${remaining.toFixed(2)}`,
      online: s.budget?.online ?? false,
      detail: s.budget?.detail ?? `$${used.toFixed(2)} / $${limit.toFixed(2)}`,
      onClick: () => emit('badge-click', 'budget'),
    },
  ]
})
</script>

<style scoped>
.status-badges {
  display: flex;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
  align-items: center;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.status-badges--loading {
  justify-content: center;
  padding: var(--usx-spacing-md);
}

.status-badges__loading {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.status-badge {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs, 4px);
  padding: 2px var(--usx-spacing-sm, 8px);
  border-radius: var(--usx-radius-sm, 4px);
  font-size: var(--usx-font-size-xs, 0.75rem);
  font-weight: var(--usx-font-weight-medium, 500);
  transition: background 0.15s ease;
  user-select: none;
}

.status-badge:hover {
  background: var(--usx-color-surface-hover, rgba(255, 255, 255, 0.05));
}

.status-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot--online {
  background: var(--usx-color-success);
  box-shadow: 0 0 4px var(--usx-color-success);
}

.dot--offline {
  background: var(--usx-color-danger);
}

.status-badge__label {
  color: var(--usx-color-on-surface);
  white-space: nowrap;
}
</style>