<template>
  <div>
    <h3 class="surface__panel-title">Budget and Usage</h3>
    <div class="budget-overview">
      <div class="budget-stat">
        <span class="budget-stat-label">Remaining</span>
        <span class="budget-stat-value">${{ srv.budgetRemaining != null ? srv.budgetRemaining.toFixed(2) : '—' }}</span>
      </div>
      <div class="budget-stat">
        <span class="budget-stat-label">Monthly Limit</span>
        <span class="budget-stat-value">${{ srv.budgetLimit.toFixed(2) }}</span>
      </div>
      <div class="budget-stat">
        <span class="budget-stat-label">Used</span>
        <span class="budget-stat-value">${{ srv.budgetUsed.toFixed(2) }}</span>
      </div>
      <div class="budget-stat">
        <span class="budget-stat-label">Status</span>
        <UBadge :type="srv.budgetOverLimit ? 'error' : 'success'" size="sm">
          {{ srv.budgetOverLimit ? 'OVER LIMIT' : 'OK' }}
        </UBadge>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useServerStore } from '../../../stores/server'
import UBadge from '../../../skills/atoms/UBadge.vue'

const srv = useServerStore()
</script>

<style scoped>
.budget-overview { --server-budget-column-min: calc(var(--usx-touch-min) * 4.5); display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--server-budget-column-min)), 1fr)); gap: var(--usx-spacing-md); min-width: 0; }
.budget-stat { padding: var(--usx-spacing-md); border-radius: var(--usx-radius-lg); background: var(--usx-color-background); display: flex; flex-direction: column; gap: var(--usx-spacing-xs); min-width: 0; }
.budget-stat-label { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); text-transform: uppercase; }
.budget-stat-value { font-size: var(--usx-font-size-2xl); font-weight: var(--usx-font-weight-bold); overflow-wrap: anywhere; }
</style>