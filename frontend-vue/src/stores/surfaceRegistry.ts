/**
 * @module stores/surfaceRegistry
 * @description Surface Registry store — ecosystem health, discovery, wiring.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = '/api/surfaces'

export interface SurfaceInfo {
  name: string
  component: string
  route: string
  icon: string
  devTab: boolean
  devOnly: boolean
  description: string
  runtimes: string[]
  panels: string[]
  exists?: boolean
  issues?: string[]
  warnings?: string[]
  clean?: boolean
}

export interface BackendRuntime {
  service: string
  file: string
  protocols: string[]
  endpoints: string[]
}

export interface RegistryReport {
  ecosystem: {
    total_surfaces: number
    health: string
    detached: string[]
    phantom: string[]
    untabbed: string[]
    wired_backend: string[]
  }
  validation: {
    all_clean: boolean
    total_issues: number
  }
  backends_available: string[]
  recommendations: string[]
}

export const useSurfaceRegistryStore = defineStore('surfaceRegistry', () => {
  const surfaces = ref<SurfaceInfo[]>([])
  const report = ref<RegistryReport | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const healthySurfaces = computed(() =>
    surfaces.value.filter((s) => s.clean !== false),
  )

  const unhealthySurfaces = computed(() =>
    surfaces.value.filter((s) => s.clean === false),
  )

  const wiredSurfaces = computed(() =>
    surfaces.value.filter((s) => s.runtimes.length > 0),
  )

  async function fetchReport(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/report`)
      const data = await res.json()
      if (data.success) {
        report.value = data
      } else {
        error.value = data.error || 'Failed to fetch report'
      }
    } catch (e: any) {
      error.value = e.message || 'Network error'
      console.warn('Surface registry report unavailable:', e.message)
    } finally {
      loading.value = false
    }
  }

  async function fetchDiscover(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/discover`)
      const data = await res.json()
      if (data.success) {
        // Map to SurfaceInfo array
        const names = data.surfaces || []
        surfaces.value = names.map((name: string) => ({
          name,
          component: `${name}Surface`,
          route: `/${name}`,
          icon: 'widgets',
          devTab: false,
          devOnly: false,
          description: '',
          runtimes: data.wired_backend?.includes(name) ? ['wired'] : [],
          panels: [],
        }))
      } else {
        error.value = data.error || 'Failed to discover surfaces'
      }
    } catch (e: any) {
      error.value = e.message || 'Network error'
      console.warn('Surface registry discover unavailable:', e.message)
    } finally {
      loading.value = false
    }
  }

  async function scaffold(name: string): Promise<any> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/scaffold`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      })
      const data = await res.json()
      if (!data.success) {
        error.value = data.error || 'Scaffold failed'
      }
      return data
    } catch (e: any) {
      error.value = e.message || 'Network error'
      return { success: false, error: e.message }
    } finally {
      loading.value = false
    }
  }

  async function wire(target: string, backendRuntime: string): Promise<any> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/wire`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target, backend_runtime: backendRuntime }),
      })
      const data = await res.json()
      if (!data.success) {
        error.value = data.error || 'Wire failed'
      }
      return data
    } catch (e: any) {
      error.value = e.message || 'Network error'
      return { success: false, error: e.message }
    } finally {
      loading.value = false
    }
  }

  return {
    surfaces,
    report,
    loading,
    error,
    healthySurfaces,
    unhealthySurfaces,
    wiredSurfaces,
    fetchReport,
    fetchDiscover,
    scaffold,
    wire,
  }
})