<template>
  <div class="app-shell" :class="{ 'sidebar-open': shell.sidebarOpen }">
    <GlobalToolbar
      :tabs="currentTabs"
      :chat-mode="shell.chatMode"
      :sidebar-open="shell.sidebarOpen"
      @toggle-chat="shell.toggleChat"
      @toggle-sidebar="shell.toggleSidebar"
    />
    <div class="app-body">
      <aside v-if="shell.sidebarOpen" class="app-sidebar">
        <FilepickerSidebar />
      </aside>
      <main class="app-main">
        <router-view />
      </main>
    </div>
    <!-- Floating Chat -->
    <FloatingChat
      v-if="shell.chatMode === 'floating'"
      @close="shell.setChatMode('closed')"
    />
    <!-- Snackbar Host -->
    <SnackbarHost />
  </div>
</template>

<script setup lang="ts">
/**
 * @component AppShell
 * @description Root layout — toolbar + sidebar + router-view + floating chat + snackbar.
 * Replaces RootLayout + SurfaceShellContext from React.
 * @category layouts
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useShellStore } from '../stores/shell'
import GlobalToolbar from '../skills/organisms/GlobalToolbar.vue'
import FilepickerSidebar from '../skills/molecules/FilepickerSidebar.vue'
import FloatingChat from '../surfaces/assistui/FloatingChat.vue'
import SnackbarHost from '../skills/molecules/SnackbarHost.vue'

const route = useRoute()
const shell = useShellStore()

const currentTabs = computed(() => {
  // Surface-specific tabs can be injected via route meta
  return (route.meta.tabs as any[]) || []
})
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  overflow: hidden;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  height: 0; /* force flex child to respect parent */
}

.app-sidebar {
  width: var(--usx-sidebar-width);
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  background: var(--pico-card-background-color);
  border-right: 1px solid var(--pico-border-color);
}

.app-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
}
</style>
