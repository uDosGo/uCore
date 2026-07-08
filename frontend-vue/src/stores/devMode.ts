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

  /** Fetch mode from backend. Falls back to localStorage if offline. */
  async function probe(): Promise<void> {
    loading.value = true
    try {
      const res = await fetch(`${API}/api/dev-layer/state`, { signal: AbortSignal.timeout(1500) })
      if (res.ok) {
        const data = await res.json()
        if (data?.mode) {
          mode.value = data.mode as DevModeState
          localStorage.setItem('ucore-dev-mode', data.mode)
          loading.value = false
          return
        }
      }
    } catch { /* backend offline, use localStorage */ }
    // Fallback: check localStorage
    const saved = localStorage.getItem('ucore-dev-mode')
    if (saved === 'on' || saved === 'minimal') {
      mode.value = saved as DevModeState
    }
    loading.value = false
  }

  async function setMode(m: DevModeState): Promise<void> {
    mode.value = m
    localStorage.setItem('ucore-dev-mode', m)
    try {
      await fetch(`${API}/api/dev-layer/state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: m }),
        signal: AbortSignal.timeout(1500),
      })
    } catch { /* offline — local state is already set */ }
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
