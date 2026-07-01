/**
 * @module stores/devMode
 * @description Dev Layer — 3-state mode toggle (OFF / MINIMAL / ON).
 * Synced with backend /api/dev-layer/state and /api/dev-layer/toggle.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type DevModeState = 'off' | 'minimal' | 'on'

const API_BASE = 'http://localhost:8484'

async function apiGet(path: string): Promise<any> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`)
  return res.json()
}

async function apiPut(path: string, body: any): Promise<any> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`PUT ${path}: ${res.status}`)
  return res.json()
}

async function apiPost(path: string, body: any): Promise<any> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path}: ${res.status}`)
  return res.json()
}

export const useDevModeStore = defineStore('devMode', () => {
  const mode = ref<DevModeState>('off')
  const devServerRunning = ref(false)
  const probing = ref(false)
  const probed = ref(false)

  async function probe(): Promise<boolean> {
    probing.value = true
    try {
      const response = await fetch(`${API_BASE}/api/health`, { method: 'GET' })
      devServerRunning.value = response.ok
      if (devServerRunning.value) {
        await syncFromBackend()
      }
    } catch {
      devServerRunning.value = false
      mode.value = 'off'
    } finally {
      probing.value = false
      probed.value = true
    }
    return devServerRunning.value
  }

  async function syncFromBackend(): Promise<void> {
    try {
      const data = await apiGet('/api/dev-layer/state')
      if (data && data.mode) {
        mode.value = data.mode as DevModeState
      }
    } catch {
      // backend route not available — stay local
    }
  }

  async function setMode(newMode: DevModeState): Promise<void> {
    try {
      const data = await apiPut('/api/dev-layer/state', { mode: newMode })
      if (data && data.mode) {
        mode.value = data.mode as DevModeState
      }
    } catch {
      mode.value = newMode
    }
  }

  async function toggle(): Promise<void> {
    try {
      const data = await apiPost('/api/dev-layer/toggle', {})
      if (data && data.mode) {
        mode.value = data.mode as DevModeState
      }
    } catch {
      const cycle: DevModeState[] = ['off', 'minimal', 'on']
      const idx = cycle.indexOf(mode.value)
      mode.value = cycle[(idx + 1) % cycle.length]
    }
  }

  async function enable(): Promise<void> { await setMode('on') }
  async function disable(): Promise<void> { await setMode('off') }

  const isDevSurface = computed(() => (_surfaceId: string) => mode.value === 'on')
  const showDevContent = computed(() => devServerRunning.value && mode.value === 'on')
  const isMinimal = computed(() => mode.value === 'minimal')
  const isFullyEnabled = computed(() => mode.value === 'on')

  return {
    mode, devServerRunning, probing, probed,
    probe, toggle, enable, disable, setMode, syncFromBackend,
    isDevSurface, showDevContent, isMinimal, isFullyEnabled,
  }
})
