/**
 * @module stores/shell
 * @description App shell state — sidebar, chat panel, last surface.
 * Ported from SurfaceShellContext.tsx (React).
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ChatMode = 'closed' | 'panel' | 'floating'

export const useShellStore = defineStore('shell', () => {
  const sidebarOpen = ref(false)
  const chatMode = ref<ChatMode>('closed')
  const lastSurface = ref<string>('/')

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function setSidebarOpen(open: boolean) {
    sidebarOpen.value = open
  }

  function setChatMode(mode: ChatMode) {
    chatMode.value = mode
  }

  function toggleChat() {
    chatMode.value = chatMode.value === 'closed' ? 'floating' : 'closed'
  }

  function setLastSurface(route: string) {
    lastSurface.value = route
  }

  return {
    sidebarOpen,
    chatMode,
    lastSurface,
    toggleSidebar,
    setSidebarOpen,
    setChatMode,
    toggleChat,
    setLastSurface,
  }
})
