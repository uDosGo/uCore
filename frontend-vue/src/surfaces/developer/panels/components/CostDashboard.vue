<template>
  <div class="cost-dashboard">
    <span class="cost-dashboard__title">Cost Dashboard</span>

    <div v-if="!cost" class="cost-dashboard__loading">Loading...</div>
    <div v-else class="cost-dashboard__bars">
      <div class="cost-bar">
        <div class="cost-bar__labels">
          <span>Today</span>
          <span class="cost-bar__amount">
            ${{ dailyUsed.toFixed(2) }} / ${{ dailyLimit.toFixed(2) }}
          </span>
        </div>
        <progress
          class="cost-bar__progress"
          :class="{ 'cost-bar__progress--warn': dailyPct > 80, 'cost-bar__progress--danger': dailyPct > 95 }"
          :value="Math.min(dailyPct, 100)"
          max="100"
        />
      </div>

      <div class="cost-bar" v-if="weeklyUsed > 0 || weeklyLimit > 0">
        <div class="cost-bar__labels">
          <span>Week</span>
          <span class="cost-bar__amount">
            ${{ weeklyUsed.toFixed(2) }} / ${{ weeklyLimit.toFixed(2) }}
          </span>
        </div>
        <progress
          class="cost-bar__progress cost-bar__progress--secondary"
          :value="Math.min(weeklyPct, 100)"
          max="100"
        />
      </div>

      <div class="cost-bar" v-if="monthlyUsed > 0 || monthlyLimit > 0">
        <div class="cost-bar__labels">
          <span>Month</span>
          <span class="cost-bar__amount">
            ${{ monthlyUsed.toFixed(2) }} / ${{ monthlyLimit.toFixed(2) }}
          </span>
        </div>
        <progress
          class="cost-bar__progress cost-bar__progress--tertiary"
          :value="Math.min(monthlyPct, 100)"
          max="100"
        />
      </div>
    </div>

    <div v-if="topModels.length > 0" class="cost-dashboard__models">
      <span class="cost-dashboard__subtitle">Top Models</span>
      <div v-for="m in topModels" :key="m.name" class="cost-model-row">
        <span class="cost-model-row__name">{{ m.name }}</span>
        <span class="cost-model-row__cost">${{ (m.cost || 0).toFixed(2) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface TopModel {
  name: string
  cost?: number
}

const props = defineProps<{
  cost: {
    daily?: { used?: number; limit?: number }
    weekly?: { used?: number; limit?: number }
    monthly?: { used?: number; limit?: number }
    top_models?: TopModel[]
  } | null
}>()

const dailyUsed = computed(() => props.cost?.daily?.used ?? 0)
const dailyLimit = computed(() => props.cost?.daily?.limit ?? 2)
const weeklyUsed = computed(() => props.cost?.weekly?.used ?? 0)
const weeklyLimit = computed(() => props.cost?.weekly?.limit ?? 10)
const monthlyUsed = computed(() => props.cost?.monthly?.used ?? 0)
const monthlyLimit = computed(() => props.cost?.monthly?.limit ?? 30)

const dailyPct = computed(() => (dailyLimit.value > 0 ? (dailyUsed.value / dailyLimit.value) * 100 : 0))
const weeklyPct = computed(() => (weeklyLimit.value > 0 ? (weeklyUsed.value / weeklyLimit.value) * 100 : 0))
const monthlyPct = computed(() => (monthlyLimit.value > 0 ? (monthlyUsed.value / monthlyLimit.value) * 100 : 0))

const topModels = computed(() => props.cost?.top_models ?? [])
</script>

<style scoped>
.cost-dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.cost-dashboard__title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.cost-dashboard__loading {
  padding: var(--usx-spacing-lg);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.cost-dashboard__bars {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.cost-bar {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.cost-bar__labels {
  display: flex;
  justify-content: space-between;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.cost-bar__amount {
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-on-surface);
}

.cost-bar__progress {
  --cost-fill-color: var(--usx-color-primary);
  width: 100%;
  height: var(--usx-spacing-sm);
  appearance: none;
  border: none;
  background: var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  overflow: hidden;
}

.cost-bar__progress::-webkit-progress-bar {
  background: var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
}

.cost-bar__progress::-webkit-progress-value {
  background: var(--cost-fill-color);
  border-radius: var(--usx-radius-sm);
  transition: width var(--usx-transition-fast);
}

.cost-bar__progress::-moz-progress-bar {
  background: var(--cost-fill-color);
  border-radius: var(--usx-radius-sm);
  transition: width var(--usx-transition-fast);
}

.cost-bar__progress--warn { --cost-fill-color: var(--usx-color-warning); }
.cost-bar__progress--danger { --cost-fill-color: var(--usx-color-danger); }
.cost-bar__progress--secondary { --cost-fill-color: var(--usx-color-success); }
.cost-bar__progress--tertiary { --cost-fill-color: var(--usx-color-accent); }

.cost-dashboard__models {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.cost-dashboard__subtitle {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
}

.cost-model-row {
  display: flex;
  justify-content: space-between;
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-1) 0;
}

.cost-model-row__name {
  color: var(--usx-color-on-surface);
}

.cost-model-row__cost {
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-on-surface-muted);
}
</style>