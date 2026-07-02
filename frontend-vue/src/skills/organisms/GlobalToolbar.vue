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
        @click="shell.toggleTabOrientation()"
        :title="shell.tabOrientation === 'horizontal' ? 'Switch to vertical tab layout' : 'Switch to horizontal tab layout'"
      >
        <UIcon :name="shell.tabOrientation === 'horizontal' ? 'swap_vert' : 'swap_horiz'" class="global-toolbar__icon" />
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
      <button
        class="global-toolbar__tab global-toolbar__tab--nav"
        :class="{ 'global-toolbar__tab--active': route.path.includes('/terminal') }"
        @click="navigate('/terminal')"
        title="Terminal"
      >
        <UIcon name="terminal" class="global-toolbar__icon" />
      </button>
    </div>

    <!-- Middle: always empty — surface tab navigation is now handled by SurfaceTabNav below -->
    <div class="global-toolbar__center"></div>

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
 * Center is now always empty — surface tab navigation has been moved
 * to the SurfaceTabNav component rendered by each surface.
 * @category organisms
 */
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useShellStore } from '../../stores/shell'
import { useDevModeStore } from '../../stores/devMode'
import { useSettingsStore } from '../../stores/settings'
import UIcon from '../atoms/UIcon.vue'
import UBadge from '../atoms/UBadge.vue'

interface Props {
  chatMode?: string
  sidebarOpen?: boolean
}

const emit = defineEmits<{
  'toggle-chat': []
  'toggle-sidebar': []
}>()

const router = useRouter()
const route = useRoute()
const shell = useShellStore()
const devMode = useDevModeStore()
const settings = useSettingsStore()

const isDark = computed(() => settings.themeMode === 'dark')

function toggleTheme() {
  settings.setThemeMode(isDark.value ? 'light' : 'dark')
}

function navigate(path: string) {
  router.push(path)
}
</script>

<!-- All styles moved to usx-standard.css for consistency -->
<style scoped>
/* GlobalToolbar styles are defined in usx-standard.css under "GLOBAL TOOLBAR" section.
   This ensures consistent tab styling across all surfaces. */
</style>
