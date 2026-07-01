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

    <p class="usx-mt-sm" style="color: var(--usx-color-on-surface-muted)">
      Central registry for all uCore surfaces. Discover, validate,
      scaffold, and wire frontend surfaces to backend runtimes.
    </p>

    <!-- Loading -->
    <div v-if="store.loading" class="usx-flex-center usx-p-lg">
      <span class="material-symbols-outlined" style="font-size: var(--usx-icon-size-xl); animation: spin 1s linear infinite">progress_activity</span>
      <span style="color: var(--usx-color-on-surface-muted)">Loading registry...</span>
    </div>

    <!-- Error -->
    <div v-else-if="store.error" class="usx-compact usx-mt-md" style="border: var(--usx-border-width) solid var(--usx-color-danger); border-radius: var(--usx-radius-md); background: var(--usx-color-danger); color: var(--usx-color-on-danger)">
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
        <span style="font-size: var(--usx-font-size-3xl); font-weight: var(--usx-font-weight-bold)">{{ store.report.ecosystem.total_surfaces }}</span>
        <span style="color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm)">Total Surfaces</span>
      </div>
      <div class="usx-card">
        <span style="font-size: var(--usx-font-size-3xl); font-weight: var(--usx-font-weight-bold)">
          {{ store.report.ecosystem.wired_backend.length }}
        </span>
        <span style="color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm)">Backend Wired</span>
      </div>
      <div class="usx-card">
        <span style="font-size: var(--usx-font-size-3xl); font-weight: var(--usx-font-weight-bold)">
          {{ store.report.backends_available.length }}
        </span>
        <span style="color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm)">Runtimes Available</span>
      </div>
      <div class="usx-card">
        <span
          style="font-size: var(--usx-font-size-3xl); font-weight: var(--usx-font-weight-bold)"
          :style="{ color: store.report.validation.total_issues === 0 ? 'var(--usx-color-success)' : 'var(--usx-color-warning)' }"
        >
          {{ store.report.validation.total_issues }}
        </span>
        <span style="color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm)">Issues</span>
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
    <div v-if="store.report?.recommendations?.length" class="usx-compact usx-mt-md" style="border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md)">
      <div class="usx-flex-row">
        <span class="material-symbols-outlined" style="color: var(--usx-color-primary)">tips_and_updates</span>
        <span style="font-weight: var(--usx-font-weight-semibold)">Recommendations</span>
      </div>
      <ul class="usx-mt-sm" style="padding-left: var(--usx-spacing-lg); margin: 0; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm)">
        <li
          v-for="(rec, i) in store.report.recommendations"
          :key="i"
          style="margin-bottom: var(--usx-spacing-xs)"
        >
          {{ rec }}
        </li>
      </ul>
    </div>

    <!-- Scaffold Form -->
    <div class="usx-compact usx-mt-lg" style="border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md)">
      <div class="usx-flex-row">
        <span class="material-symbols-outlined" style="color: var(--usx-color-primary)">add_circle</span>
        <span style="font-weight: var(--usx-font-weight-semibold)">Scaffold New Surface</span>
      </div>
      <div class="usx-flex-row usx-mt-sm">
        <input
          v-model="scaffoldName"
          type="text"
          placeholder="surface-name (kebab-case)"
          style="flex: 1; min-height: var(--usx-input-height)"
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
      <div v-if="scaffoldResult" class="usx-mt-sm" style="font-size: var(--usx-font-size-sm)">
        <div v-if="scaffoldResult.success" style="color: var(--usx-color-success)">
          Surface scaffolded: {{ scaffoldResult.name }}
        </div>
        <div v-else style="color: var(--usx-color-danger)">
          {{ scaffoldResult.error }}
        </div>
        <div v-if="scaffoldResult.instructions" class="usx-mt-sm">
          <div style="font-weight: var(--usx-font-weight-semibold); margin-bottom: var(--usx-spacing-xs)">Next steps:</div>
          <ol style="padding-left: var(--usx-spacing-lg); margin: 0; color: var(--usx-color-on-surface-muted)">
            <li v-for="(step, i) in scaffoldResult.instructions" :key="i" style="margin-bottom: var(--usx-spacing-xs)">
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
            <span class="material-symbols-outlined" style="font-size: var(--usx-icon-size-sm)">memory</span>
            <span style="font-weight: var(--usx-font-weight-medium)">{{ runtime }}</span>
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
              <span class="material-symbols-outlined" style="font-size: var(--usx-icon-size-sm)">{{ surface.icon || 'widgets' }}</span>
              <span style="font-weight: var(--usx-font-weight-medium)">{{ surface.name }}</span>
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
</style>