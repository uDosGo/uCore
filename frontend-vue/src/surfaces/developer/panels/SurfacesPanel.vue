<template>
  <div class="usx-section">
    <div class="usx-flex-between">
      <h3>Surface Registry</h3>
      <div class="usx-flex-row usx-gap-sm">
        <span
          v-if="store.report?.ecosystem"
          class="usx-badge"
          :class="healthBadgeClass"
        >
          {{ store.report?.ecosystem.health }}
        </span>
        <button class="usx-btn--primary" @click="refresh">
          <span class="material-symbols-outlined">refresh</span>
          Refresh
        </button>
      </div>
    </div>

    <p class="usx-mt-sm surfaces-muted-copy">
      Central registry for all uCore surfaces. Discover, validate,
      scaffold, and wire frontend surfaces to backend runtimes.
    </p>

    <!-- Loading -->
    <div v-if="store.loading" class="usx-flex-center usx-p-lg">
      <span class="material-symbols-outlined surfaces-spinner">progress_activity</span>
      <span class="surfaces-muted-copy">Loading registry...</span>
    </div>

    <!-- Error -->
    <div v-else-if="store.error" class="usx-compact usx-mt-md surfaces-error-box">
      <div class="usx-flex-row">
        <span class="material-symbols-outlined">error</span>
        <span>{{ store.error }}</span>
      </div>
      <button class="usx-btn--primary usx-mt-sm" @click="refresh">
        Retry
      </button>
    </div>

    <!-- Ecosystem Summary -->
    <div v-if="store.report?.ecosystem" class="usx-grid usx-grid--dense usx-mt-md">
      <div class="usx-card">
        <span class="surfaces-stat-value">{{ store.report.ecosystem.total_surfaces }}</span>
        <span class="surfaces-stat-label">Total Surfaces</span>
      </div>
      <div class="usx-card">
        <span class="surfaces-stat-value">
          {{ store.report.ecosystem.wired_backend.length }}
        </span>
        <span class="surfaces-stat-label">Backend Wired</span>
      </div>
      <div class="usx-card">
        <span class="surfaces-stat-value">
          {{ store.report.backends_available.length }}
        </span>
        <span class="surfaces-stat-label">Runtimes Available</span>
      </div>
      <div class="usx-card">
        <span
          class="surfaces-stat-value"
          :class="issuesStatClass"
        >
          {{ store.report.validation.total_issues }}
        </span>
        <span class="surfaces-stat-label">Issues</span>
      </div>
    </div>

    <!-- Alerts -->
    <div v-if="store.report?.ecosystem" class="usx-mt-md">
      <div
        v-if="store.report.ecosystem.detached.length"
        class="usx-badge usx-badge--error usx-mr-sm"
      >
        {{ store.report.ecosystem.detached.length }} detached
      </div>
      <div
        v-if="store.report.ecosystem.phantom.length"
        class="usx-badge usx-badge--error usx-mr-sm"
      >
        {{ store.report.ecosystem.phantom.length }} phantom
      </div>
      <div
        v-if="store.report.ecosystem.untabbed.length"
        class="usx-badge usx-badge--error usx-mr-sm"
      >
        {{ store.report.ecosystem.untabbed.length }} untabbed
      </div>
    </div>

    <!-- Recommendations -->
    <div v-if="store.report?.recommendations?.length" class="usx-compact usx-mt-md surfaces-box">
      <div class="usx-flex-row">
        <span class="material-symbols-outlined surfaces-icon-primary">tips_and_updates</span>
        <span class="surfaces-heading-strong">Recommendations</span>
      </div>
      <ul class="usx-mt-sm surfaces-list">
        <li
          v-for="(rec, i) in store.report.recommendations"
          :key="i"
          class="surfaces-list-item"
        >
          {{ rec }}
        </li>
      </ul>
    </div>

    <!-- Scaffold Form -->
    <div class="usx-compact usx-mt-lg surfaces-box">
      <div class="usx-flex-row">
        <span class="material-symbols-outlined surfaces-icon-primary">add_circle</span>
        <span class="surfaces-heading-strong">Scaffold New Surface</span>
      </div>
      <div class="usx-flex-row usx-mt-sm">
        <input
          v-model="scaffoldName"
          type="text"
          placeholder="surface-name (kebab-case)"
          class="surfaces-input"
          @keyup.enter="doScaffold"
        />
        <button
          class="usx-btn--primary"
          :disabled="!scaffoldName || store.loading"
          @click="doScaffold"
        >
          <span class="material-symbols-outlined">rocket_launch</span>
          Scaffold
        </button>
      </div>
      <div v-if="scaffoldResult" class="usx-mt-sm surfaces-result-copy">
        <div v-if="scaffoldResult.success" class="surfaces-success-copy">
          Surface scaffolded: {{ scaffoldResult.name }}
        </div>
        <div v-else class="surfaces-danger-copy">
          {{ scaffoldResult.error }}
        </div>
        <div v-if="scaffoldResult.instructions" class="usx-mt-sm">
          <div class="surfaces-heading-strong surfaces-mb-xs">Next steps:</div>
          <ol class="surfaces-list surfaces-list--ordered">
            <li v-for="(step, i) in scaffoldResult.instructions" :key="i" class="surfaces-list-item">
              {{ step }}
            </li>
          </ol>
        </div>
      </div>
    </div>

    <!-- Backend Runtimes -->
    <div v-if="store.report?.backends_available?.length" class="usx-mt-lg">
      <div class="usx-flex-between">
        <h4>Available Backend Runtimes</h4>
        <span class="usx-badge usx-badge--accent">{{ store.report.backends_available.length }} runtimes</span>
      </div>
      <div class="usx-grid usx-grid--dense usx-mt-sm">
        <div
          v-for="runtime in store.report.backends_available"
          :key="runtime"
          class="usx-card"
        >
          <div class="usx-flex-row">
            <span class="material-symbols-outlined surfaces-icon-sm">memory</span>
            <span class="surfaces-label-medium">{{ runtime }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Surface List -->
    <div v-if="store.surfaces.length" class="usx-mt-lg">
      <div class="usx-flex-between">
        <h4>Registered Surfaces ({{ store.surfaces.length }})</h4>
      </div>
      <div class="usx-grid usx-grid--dense usx-mt-sm">
        <div
          v-for="surface in store.surfaces"
          :key="surface.name"
          class="usx-card"
        >
          <div class="usx-flex-between">
            <div class="usx-flex-row">
              <span class="material-symbols-outlined surfaces-icon-sm">{{ surface.icon || 'widgets' }}</span>
              <span class="surfaces-label-medium">{{ surface.name }}</span>
            </div>
            <span
              v-if="surface.clean === false"
              class="usx-badge usx-badge--error"
            >
              {{ surface.issues?.length }} issues
            </span>
            <span
              v-else-if="surface.runtimes.length > 0"
              class="usx-badge usx-badge--accent"
            >
              wired
            </span>
            <span
              v-else
              class="usx-badge"
            >
              registered
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useSurfaceRegistryStore } from '../../../stores/surfaceRegistry'

const store = useSurfaceRegistryStore()
const scaffoldName = ref('')
const scaffoldResult = ref<any>(null)

const healthBadgeClass = computed(() => {
  const health = store.report?.ecosystem?.health
  if (health === 'healthy') return 'usx-badge--accent'
  return 'usx-badge--error'
})

const issuesStatClass = computed(() => {
  return store.report?.validation?.total_issues === 0
    ? 'surfaces-success-copy'
    : 'surfaces-warning-copy'
})

async function refresh() {
  scaffoldResult.value = null
  await store.fetchReport()
  await store.fetchDiscover()
}

async function doScaffold() {
  if (!scaffoldName.value) return
  scaffoldResult.value = await store.scaffold(scaffoldName.value)
  if (scaffoldResult.value?.success) {
    scaffoldName.value = ''
  }
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.surfaces-muted-copy {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.surfaces-spinner {
  font-size: var(--usx-icon-size-xl);
  animation: spin var(--usx-motion-duration-spin) linear infinite;
}

.surfaces-error-box {
  border: var(--usx-border-width) solid var(--usx-color-danger);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-danger);
  color: var(--usx-color-on-danger);
}

.surfaces-stat-value {
  font-size: var(--usx-font-size-3xl);
  font-weight: var(--usx-font-weight-bold);
}

.surfaces-stat-label {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.surfaces-box {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
}

.surfaces-icon-primary {
  color: var(--usx-color-primary);
}

.surfaces-icon-sm {
  font-size: var(--usx-icon-size-sm);
}

.surfaces-heading-strong {
  font-weight: var(--usx-font-weight-semibold);
}

.surfaces-mb-xs {
  margin-bottom: var(--usx-spacing-xs);
}

.surfaces-list {
  padding-left: var(--usx-spacing-lg);
  margin: 0;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.surfaces-list--ordered {
  list-style: decimal;
}

.surfaces-list-item {
  margin-bottom: var(--usx-spacing-xs);
}

.surfaces-input {
  flex: 1;
  min-height: var(--usx-touch-min);
}

.surfaces-result-copy {
  font-size: var(--usx-font-size-sm);
}

.surfaces-success-copy {
  color: var(--usx-color-success);
}

.surfaces-danger-copy {
  color: var(--usx-color-danger);
}

.surfaces-warning-copy {
  color: var(--usx-color-warning);
}

.surfaces-label-medium {
  font-weight: var(--usx-font-weight-medium);
}
</style>