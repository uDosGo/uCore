<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <!-- Hub navigation: quick-launch links to key surfaces -->
    <SurfaceTabNav
      v-model="activeHubTab"
      :tabs="visibleHubTabs"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content">
      <div class="dashboard-surface">
        <h1 class="dashboard-surface__title">Dashboard</h1>
        <p class="dashboard-surface__subtitle">Select a surface to begin</p>

        <div class="dashboard-surface__grid-inner">
          <SurfaceCard
            v-for="surface in visibleSurfaces"
            :key="surface.id"
            :surface="surface"
            @click="navigate(surface.route)"
          />
        </div>

        <!-- Dev Mode hint when backend is reachable but Dev Mode is off -->
        <div v-if="devMode.isOffline" class="dashboard-surface__dev-hint">
          <p>
            <UIcon name="code" />
            Developer tools are available.
            <button class="dashboard-surface__dev-link" @click="devMode.setMode('on')">Enable Dev Mode</button>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component DashboardSurface
 * @description Mission Control — surface hub dashboard with surface cards and hub navigation.
 * Ported from DashboardSurface.tsx (React).
 * Enhanced with Dev Mode filtering — dev-only surfaces hidden when Dev Mode is off.
 * @category surfaces
 * @usage Routed at '/' — default landing page.
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useShellStore } from '../../stores/shell'
import { useDevModeStore } from '../../stores/devMode'
import SurfaceCard from '../../skills/molecules/SurfaceCard.vue'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import type { SurfaceCard as SurfaceCardType } from '../../types'

const router = useRouter()
const shell = useShellStore()
const devMode = useDevModeStore()

// Hub navigation tabs
const HUB_TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: 'home' },
  { id: 'missions', label: 'Missions', icon: 'flag' },
  { id: 'snackmachine', label: 'Snacks', icon: 'snack' },
  { id: 'server', label: 'Server', icon: 'server' },
  { id: 'system', label: 'System', icon: 'settings' },
  { id: 'developer', label: 'Developer', icon: 'code' },
]

const activeHubTab = ref('dashboard')

const visibleHubTabs = computed(() =>
  HUB_TABS.filter(t => t.id !== 'developer' || !devMode.isOffline)
)

watch(activeHubTab, (tabId) => {
  if (!tabId || tabId === 'dashboard') return
  const routes: Record<string, string> = {
    missions: '/workflow?tab=mission-control',
    server: '/server',
    snackmachine: '/snackmachine',
    system: '/system',
    developer: '/developer',
  }
  const path = routes[tabId]
  if (path) router.push(path)
})

const ALL_SURFACES: SurfaceCardType[] = [
  { id: 'assistui', title: 'Assistant', description: 'Agent Assisted Workflows', icon: 'bolt', route: '/assistui', color: 'var(--usx-color-accent)' },
  { id: 'ucode', title: 'uCode', description: 'GridCore — Grid, Teletext & Terminal', icon: 'grid', route: '/ucode', color: 'var(--usx-color-success)' },
  { id: 'server', title: 'Server', description: 'Backend Operations & Services', icon: 'server', route: '/server', color: 'var(--usx-color-warning)' },
  { id: 'workflow', title: 'Workflow', description: 'Missions, Tasks & Binder', icon: 'workflow', route: '/workflow', color: 'var(--usx-color-primary)' },
  { id: 'system', title: 'System', description: 'Admin, Pages & Tools', icon: 'settings', route: '/system', color: 'var(--usx-color-on-surface-muted)' },
  { id: 'documentation', title: 'Documentation', description: 'Learning Hub & Guides', icon: 'help', route: '/documentation', color: 'var(--usx-color-accent)' },
  { id: 'snackmachine', title: 'Snack Machine', description: 'Snack/MCP/Vault Scheduler', icon: 'snack', route: '/snackmachine', color: 'var(--usx-color-danger)' },
  { id: 'browserui', title: 'Browser', description: 'Web Reader & Bookmarks', icon: 'globe', route: '/browserui', color: 'var(--usx-color-info)' },
]

const DEV_SURFACES: SurfaceCardType[] = [
  { id: 'developer', title: 'Developer', description: 'Dev Lane — Models, Agents, Kanban', icon: 'code', route: '/developer', color: 'var(--usx-color-danger)' },
]

const visibleSurfaces = computed(() => {
  const base = [...ALL_SURFACES]
  if (devMode.showDevContent) {
    base.push(...DEV_SURFACES)
  }
  return base
})

onMounted(async () => {
  await devMode.probe()
})

function navigate(route: string) {
  router.push(route)
}
</script>

<style scoped>
.dashboard-surface {
  max-width: var(--usx-max-width);
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.dashboard-surface__title {
  font-size: var(--usx-font-size-3xl);
  font-weight: var(--usx-font-weight-bold);
  margin-bottom: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
}

.dashboard-surface__subtitle {
  color: var(--usx-color-on-surface-muted);
  margin-bottom: var(--usx-spacing-md);
  font-size: var(--usx-font-size-base);
}

.dashboard-surface__grid-inner {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--usx-grid-min-col-width), 1fr));
  gap: var(--usx-grid-gap-lg);
  width: 100%;
  gap: var(--usx-spacing-md);
}

.dashboard-surface__dev-hint {
  margin-top: var(--usx-spacing-xl);
  padding: var(--usx-spacing-md);
  background: rgba(88, 166, 255, 0.05);
  border: 1px solid rgba(88, 166, 255, 0.15);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.dashboard-surface__dev-hint p {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin: 0;
}

.dashboard-surface__dev-link {
  background: none;
  border: none;
  color: var(--usx-color-primary);
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
  padding: 0;
}

.dashboard-surface__dev-link:hover {
  color: var(--usx-color-primary-hover);
}
</style>
