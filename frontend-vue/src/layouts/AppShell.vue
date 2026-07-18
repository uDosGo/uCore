<template>
  <div class="app-shell" :class="{ 'sidebar-open': shell.sidebarOpen }">
    <GlobalToolbar
      :chat-mode="shell.chatMode"
      :sidebar-open="shell.sidebarOpen"
      @toggle-chat="shell.toggleChat"
      @toggle-sidebar="shell.toggleSidebar"
    />
    <div class="app-body">
      <aside v-if="shell.sidebarOpen" class="app-sidebar">
        <FilepickerSidebar @file-select="handleFileSelect" />
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
import { useShellStore } from '../stores/shell'
import { useSettingsStore } from '../stores/settings'
import { useWorkflowStore } from '../stores/workflow'
import { useRouter } from 'vue-router'
import GlobalToolbar from '../skills/organisms/GlobalToolbar.vue'
import FilepickerSidebar from '../skills/molecules/FilepickerSidebar.vue'
import FloatingChat from '../surfaces/assistui/FloatingChat.vue'
import SnackbarHost from '../skills/molecules/SnackbarHost.vue'
import { ucoreApi } from '../api/client'
import type { FileEntry } from '../types/filepicker'

const shell = useShellStore()
const workflow = useWorkflowStore()
const router = useRouter()

// Initialize settings store to apply persisted theme (dark mode default)
useSettingsStore()

async function handleFileSelect(file: FileEntry) {
  let content = file.preview || ''
  try {
    const res = await ucoreApi.library.file(file.path)
    if (res.ok && (res.data as any)?.content !== undefined) {
      content = String((res.data as any).content || '')
    }
  } catch {
    // Fall back to indexed preview content.
  }

  workflow.selectFile({
    id: file.id || file.path,
    path: file.path,
    filename: file.filename,
    extension: file.extension,
    binder: file.binder || 'Sandbox',
    content,
    readOnly: Boolean(file.is_readonly),
  })
  await router.push({ path: '/workflow', query: { tab: 'editor' } })
}
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.app-sidebar {
  width: var(--usx-sidebar-width);
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  background: var(--usx-color-surface);
  border-right: var(--usx-border-width) solid var(--usx-color-border);
}

.app-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  padding: 0;
  background: var(--usx-color-background);
  min-height: 0;
}
</style>
