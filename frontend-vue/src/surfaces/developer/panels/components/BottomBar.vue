<template>
  <div class="bottom-bar">
    <!-- Tasker Overview -->
    <div class="bottom-bar__section">
      <UIcon name="view_kanban" class="bottom-bar__icon" />
      <div class="bottom-bar__content">
        <span class="bottom-bar__label">Tasker</span>
        <span class="bottom-bar__detail" v-if="tasker">
          {{ tasker.total }} total, {{ tasker.done }} done
        </span>
        <span class="bottom-bar__detail" v-else>—</span>
      </div>
    </div>

    <div class="bottom-bar__divider" />

    <!-- MCP Servers -->
    <div class="bottom-bar__section">
      <UIcon name="cable" class="bottom-bar__icon" />
      <div class="bottom-bar__content">
        <span class="bottom-bar__label">MCP Servers</span>
        <span class="bottom-bar__detail" v-if="mcp && mcp.length > 0">
          {{ mcpOnline }}/{{ mcp.length }} online
        </span>
        <span class="bottom-bar__detail" v-else>—</span>
      </div>
    </div>

    <div class="bottom-bar__divider" />

    <!-- Slates -->
    <div class="bottom-bar__section">
      <UIcon name="extension" class="bottom-bar__icon" />
      <div class="bottom-bar__content">
        <span class="bottom-bar__label">Slates</span>
        <span class="bottom-bar__detail" v-if="slates && slates.length > 0">
          {{ slates.length }} templates
        </span>
        <span class="bottom-bar__detail" v-else>—</span>
      </div>
    </div>

    <div class="bottom-bar__divider" />

    <!-- Next Task -->
    <div class="bottom-bar__section" v-if="tasker?.next">
      <UIcon name="my_location" class="bottom-bar__icon" />
      <div class="bottom-bar__content">
        <span class="bottom-bar__label">Next</span>
        <span class="bottom-bar__detail bottom-bar__detail--mono">{{ tasker.next }}</span>
      </div>
    </div>

    <!-- Refresh Timer -->
    <div class="bottom-bar__section bottom-bar__section--right">
      <span class="bottom-bar__detail">Updated {{ lastUpdated }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UIcon from '../../../../skills/atoms/UIcon.vue'

const props = defineProps<{
  tasker: { total?: number; done?: number; next?: string } | null
  mcp: Array<{ name: string; online?: boolean; endpoint?: string; tools?: number }> | null
  slates: Array<{ name: string; active?: boolean }> | null
  updatedAt?: string
}>()

const mcpOnline = computed(() =>
  (props.mcp || []).filter((s) => s.online !== false).length,
)

const lastUpdated = computed(() => {
  if (!props.updatedAt) return '—'
  try {
    const d = new Date(props.updatedAt)
    const now = new Date()
    const diff = Math.floor((now.getTime() - d.getTime()) / 1000)
    if (diff < 5) return 'just now'
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    return d.toLocaleTimeString()
  } catch {
    return '—'
  }
})
</script>

<style scoped>
.bottom-bar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  flex-wrap: wrap;
}

.bottom-bar__section {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.bottom-bar__section--right {
  margin-left: auto;
}

.bottom-bar__icon {
  font-size: var(--usx-font-size-base);
}

.bottom-bar__content {
  display: flex;
  flex-direction: column;
}

.bottom-bar__label {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  text-transform: uppercase;
}

.bottom-bar__detail {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.bottom-bar__detail--mono {
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-primary);
}

.bottom-bar__divider {
  width: 1px;
  height: 28px;
  background: var(--usx-color-border);
  flex-shrink: 0;
}
</style>