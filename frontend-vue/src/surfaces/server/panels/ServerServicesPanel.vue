<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">All Services</h3>
      <UButton variant="secondary" size="sm" icon="refresh" @click="srv.fetchServices">Refresh</UButton>
    </div>
    <div class="server-services-grid">
      <div v-for="svc in srv.services" :key="svc.name" class="surface__panel">
        <div class="usx-flex-row">
          <UIcon :name="svc.type === 'system' ? 'settings' : 'person'" />
          <span class="server-service-name-cell">{{ svc.name }}</span>
          <UBadge :type="svc.status === 'up' ? 'success' : svc.status === 'degraded' ? 'warning' : 'error'" size="sm">
            {{ svc.status }}
          </UBadge>
        </div>
        <p class="usx-mt-sm server-muted-text-sm">{{ svc.description }}</p>
        <div class="usx-flex-row usx-gap-md server-muted-text-sm">
          <span>Port :{{ svc.port || 'N/A' }}</span>
          <span>Uptime {{ svc.uptime }}%</span>
          <span>{{ svc.type }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useServerStore } from '../../../stores/server'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'

const srv = useServerStore()
</script>

<style scoped>
.server-muted-text-sm { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.server-service-name-cell { flex: 1; font-weight: var(--usx-font-weight-semibold); }
.server-service-name-cell { min-width: 0; overflow-wrap: anywhere; }
.server-services-grid { --server-service-column-min: calc(var(--usx-touch-min) * 4.5); display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--server-service-column-min)), 1fr)); gap: var(--usx-spacing-md); min-width: 0; }
</style>