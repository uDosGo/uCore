/**
 * @module stores/devMode
 * @description Dev Mode — 3-state toggle (OFF / MINIMAL / ON).
 * Probes /api/dev-layer/state directly — no separate health check needed.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type DevModeState = 'off' | 'minimal' | 'on'

const API = 'http://localhost:8484'

export const useDevModeStore = defineStore('devMode', () => {
  const mode = ref<DevModeState>('off')
  const loading = ref(true)

  /** Fetch mode from backend. Sets 'off' on failure. */
  async function probe(): Promise<void> {
    loading.value = true
    try {
      const res = await fetch(`${API}/api/dev-layer/state`)
      if (res.ok) {
        const data = await res.json()
        if (data?.mode) mode.value = data.mode as DevModeState
      } else {
        mode.value = 'off'
      }
    } catch {
      mode.value = 'off'
    } finally {
      loading.value = false
    }
  }

  async function setMode(m: DevModeState): Promise<void> {
    try {
      const res = await fetch(`${API}/api/dev-layer/state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: m }),
      })
      if (res.ok) {
        const data = await res.json()
        if (data?.mode) mode.value = data.mode as DevModeState
      }
    } catch { /* local state unchanged */ }
  }

  async function toggle(): Promise<void> {
    try {
      const res = await fetch(`${API}/api/dev-layer/toggle`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        if (data?.mode) mode.value = data.mode as DevModeState
      }
    } catch { /* local state unchanged */ }
  }

  const showDevContent = computed(() => mode.value === 'on')
  const isOffline = computed(() => !loading.value && mode.value === 'off')

  return { mode, loading, probe, setMode, toggle, showDevContent, isOffline }
})
