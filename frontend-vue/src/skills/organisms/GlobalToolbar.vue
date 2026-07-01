<template>
  <header class="global-toolbar">
    <!-- Left: Icon-only navigation -->
    <div class="global-toolbar__left">
      <button
        class="global-toolbar__tab global-toolbar__tab--nav"
        @click="emit('toggle-sidebar')"
        title="Finder"
      >
        <UIcon name="menu" class="global-toolbar__icon" />
      </button>
      <button
        class="global-toolbar__tab global-toolbar__tab--nav"
        :class="{ 'global-toolbar__tab--active': route.path === '/' }"
        @click="navigate('/')"
        title="Dashboard"
      >
        <UIcon name="home" class="global-toolbar__icon" />
      </button>
      <button
        class="global-toolbar__tab global-toolbar__tab--nav"
        :class="{ 'global-toolbar__tab--active': route.path.includes('/browserui') }"
        @click="navigate('/browserui')"
        title="Research"
      >
        <UIcon name="globe" class="global-toolbar__icon" />
      </button>
      <button
        class="global-toolbar__tab global-toolbar__tab--nav"
        :class="{ 'global-toolbar__tab--active': route.path.includes('/assistui') }"
        @click="navigate('/assistui')"
        title="Assistant"
      >
        <UIcon name="bolt" class="global-toolbar__icon" />
      </button>
    </div>

    <!-- Middle: Surface/context tabs -->
    <div class="global-toolbar__center">
      <button
        v-for="tab in visibleTabs"
        :key="tab.id"
        class="global-toolbar__tab"
        :class="{ 'global-toolbar__tab--active': tab.active, 'global-toolbar__tab--icon-only': compactMode }"
        @click="tab.onClick"
      >
        <UIcon :name="tab.icon" class="global-toolbar__icon" />
        <span v-if="!compactMode">{{ tab.label }}</span>
      </button>

      <!-- More tabs dropdown (when > 4 visible tabs) -->
      <span class="global-toolbar__overflow-anchor">
        <button
          v-if="overflowTabs.length > 0"
          class="global-toolbar__tab global-toolbar__more-btn"
          @click="showOverflow = !showOverflow"
          title="More tabs"
        >
          <UIcon name="more_vert" class="global-toolbar__icon" />
        </button>

        <!-- Overflow dropdown — right-aligned under the more button -->
        <div v-if="showOverflow && overflowTabs.length > 0" class="global-toolbar__overflow-dropdown">
          <button
            v-for="tab in overflowTabs"
            :key="tab.id"
            class="global-toolbar__overflow-item"
            :class="{ 'global-toolbar__overflow-item--active': tab.active }"
            @click="tab.onClick(); showOverflow = false"
          >
            <UIcon :name="tab.icon" />
            <span>{{ tab.label }}</span>
          </button>
        </div>
      </span>
    </div>

    <!-- Right: Dev Mode toggle + Theme toggle + Settings -->
    <div class="global-toolbar__right">
      <button
        v-if="devMode.devServerRunning"
        class="global-toolbar__dev-toggle"
        :class="{ 'global-toolbar__dev-toggle--on': devMode.mode === 'on' || devMode.mode === 'minimal' }"
        @click="devMode.toggle()"
        :title="(devMode.mode === 'on' || devMode.mode === 'minimal') ? 'Dev Mode ON — click to disable' : 'Dev Mode OFF — click to enable'"
      >
        <span class="global-toolbar__dev-dot"></span>
        <span class="global-toolbar__dev-label">Dev</span>
      </button>
      <UBadge v-else-if="devMode.probed" type="info">Dev Offline</UBadge>
      <UBadge v-else type="warning" title="Probing dev server...">Probing...</UBadge>
      <button
        class="global-toolbar__icon-only global-toolbar__theme-toggle"
        :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        @click="toggleTheme"
      >
        <UIcon :name="isDark ? 'light_mode' : 'dark_mode'" />
      </button>
      <button class="global-toolbar__icon-only" title="Settings" @click="navigate('/system')">
        <UIcon name="settings" />
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
/**
 * @component GlobalToolbar
 * @description Consistent top toolbar across all surfaces.
 * Overflow: when > 4 tabs, remaining tabs go into a "more" dropdown.
 * Responsive: compact icon-only mode below 900px viewport width.
 * Tabs use Pico nav-style underlined active state (styles in usx-standard.css).
 * @category organisms
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDevModeStore } from '../../stores/devMode'
import { useServerStore, SERVER_TABS } from '../../stores/server'
import { useWorkflowStore, WORKFLOW_TABS } from '../../stores/workflow'
import { useDeveloperStore, DEVELOPER_TABS } from '../../stores/developer'
import { useSettingsStore } from '../../stores/settings'
import UIcon from '../atoms/UIcon.vue'
import UBadge from '../atoms/UBadge.vue'

export interface ToolbarTab {
  id: string
  icon: string
  label: string
  active?: boolean
  onClick: () => void
}

interface Props {
  tabs?: ToolbarTab[]
  chatMode?: string
  sidebarOpen?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'toggle-chat': []
  'toggle-sidebar': []
}>()

const router = useRouter()
const route = useRoute()
const devMode = useDevModeStore()
const serverStore = useServerStore()
const workflowStore = useWorkflowStore()
const developerStore = useDeveloperStore()
const settings = useSettingsStore()
const showOverflow = ref(false)
const windowWidth = ref(window.innerWidth)

const isDark = computed(() => settings.themeMode === 'dark')

function toggleTheme() {
  settings.setThemeMode(isDark.value ? 'light' : 'dark')
}

function navigate(path: string) {
  router.push(path)
}

// Compact mode: icons only when viewport < 900px
const compactMode = computed(() => windowWidth.value < 900)

// Max 3 tabs inline — 4th slot becomes the "more" dropdown trigger.
// This ensures the dropdown always has ≥2 options when visible.
const maxVisibleTabs = 3

// Surface tabs shown in the middle of the toolbar
const surfaceTabs = computed<ToolbarTab[]>(() => {
  // If parent passed explicit tabs, use those
  if (props.tabs?.length) return props.tabs

  // On dashboard, show the main surface tabs (no Dashboard tab — it's the home icon in the left nav)
  if (route.path === '/') {
    return [
      { id: 'terminal', icon: 'terminal', label: 'Terminal', active: false, onClick: () => navigate('/terminal') },
      { id: 'missions', icon: 'flag', label: 'Missions', active: false, onClick: () => navigate('/workflow?tab=mission-control') },
      { id: 'server', icon: 'server', label: 'Server', active: false, onClick: () => navigate('/server') },
    ]
  }

  // On developer surface, show developer tabs from the developer store
  if (route.path.startsWith('/developer')) {
    return DEVELOPER_TABS.map(t => ({
      id: t.id,
      icon: t.icon,
      label: t.label,
      active: developerStore.activeTab === t.id,
      onClick: () => developerStore.setTab(t.id as any),
    }))
  }

  // On server surface, show server-specific tabs from the server store
  if (route.path.startsWith('/server')) {
    return SERVER_TABS.map(t => ({
      id: t.id,
      icon: t.icon,
      label: t.label,
      active: serverStore.activeTab === t.id,
      onClick: () => serverStore.setTab(t.id as any),
    }))
  }

  // On system surface, show system-specific tabs
  if (route.path.startsWith('/system')) {
    const sysTabs = [
      { id: 'pages', icon: 'dashboard', label: 'Pages' },
      { id: 'tools', icon: 'wrench', label: 'Tools' },
      { id: 'services', icon: 'dns', label: 'Services' },
      { id: 'variables', icon: 'tune', label: 'Variables' },
      { id: 'secrets', icon: 'key', label: 'Secrets' },
      { id: 'global-settings', icon: 'settings', label: 'Global' },
      { id: 'user-settings', icon: 'person', label: 'User' },
    ]
    const currentTab = route.query.tab || 'pages'
    return sysTabs.map(t => ({
      ...t,
      active: currentTab === t.id,
      onClick: () => navigate(`/system?tab=${t.id}`),
    }))
  }

  // On workflow surface, show workflow tabs from the workflow store
  if (route.path.startsWith('/workflow')) {
    return WORKFLOW_TABS.map(t => ({
      id: t.id,
      icon: t.icon,
      label: t.label,
      active: workflowStore.activeTab === t.id,
      onClick: () => workflowStore.setTab(t.id as any),
    }))
  }

  // On other surfaces, show nothing
  return []
})

// First maxVisibleTabs tabs shown inline
const visibleTabs = computed(() => surfaceTabs.value.slice(0, maxVisibleTabs))

// Remaining tabs go into the overflow dropdown
const overflowTabs = computed(() => surfaceTabs.value.slice(maxVisibleTabs))

// Close overflow on outside click
function onDocumentClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.global-toolbar__more-btn') && !target.closest('.global-toolbar__overflow-dropdown')) {
    showOverflow.value = false
  }
}

function onResize() {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
  window.removeEventListener('resize', onResize)
})
</script>

<!-- All styles moved to usx-standard.css for consistency -->
<style scoped>
/* GlobalToolbar styles are defined in usx-standard.css under "GLOBAL TOOLBAR" section.
   This ensures consistent tab styling across all surfaces. */
</style>
