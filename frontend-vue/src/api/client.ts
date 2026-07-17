/**
 * @module api/client
 * @description Centralized API client for all backend communication.
 * Replaces scattered fetch() calls from the React frontend.
 */

const SNACKBAR_API = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'
const UCORE_API = import.meta.env.VITE_UCORE_URL || SNACKBAR_API
const OLLAMA_API = import.meta.env.VITE_OLLAMA_URL || 'http://localhost:11434'

export interface ApiResponse<T> {
  data: T
  status: number
  ok: boolean
}

async function request<T>(url: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const data = response.ok ? await response.json() : null
  return { data, status: response.status, ok: response.ok }
}

/**
 * @description Snackbar API — clipboard, maintenance, workflows, skills
 */
export const snackbarApi = {
  baseUrl: SNACKBAR_API,
  status: () => request(`${SNACKBAR_API}/api/status`),
  clipboard: {
    list: () => request(`${SNACKBAR_API}/api/snacks/clipboard`),
    capture: (body: unknown) => request(`${SNACKBAR_API}/api/snacks/clipboard/capture`, { method: 'POST', body: JSON.stringify(body) }),
    cleanup: () => request(`${SNACKBAR_API}/api/snacks/clipboard/cleanup`, { method: 'DELETE' }),
    pin: (id: string) => request(`${SNACKBAR_API}/api/snacks/clipboard/${id}/pin`, { method: 'POST' }),
    delete: (id: string) => request(`${SNACKBAR_API}/api/snacks/clipboard/${id}`, { method: 'DELETE' }),
  },
  system: {
    maintenance: () => request(`${SNACKBAR_API}/api/system/maintenance`, { method: 'POST' }),
    workflow: (body: unknown) => request(`${SNACKBAR_API}/api/system/workflow`, { method: 'POST', body: JSON.stringify(body) }),
  },
  skills: {
    taskerSync: () => request(`${SNACKBAR_API}/api/skills/tasker_sync/run`, { method: 'POST' }),
    vaultSync: () => request(`${SNACKBAR_API}/api/skills/vault_sync/run`, { method: 'POST' }),
  },
  docker: {
    ps: () => request(`${SNACKBAR_API}/v1/docker/ps`),
  },
  exec: (command: string) => request(`${SNACKBAR_API}/v1/exec`, { method: 'POST', body: JSON.stringify({ command }) }),
}

/**
 * @description uCore backend API — knowledge, surfaces, health, library, vault
 */
export const ucoreApi = {
  baseUrl: UCORE_API,
  health: () => request(`${UCORE_API}/health`),
  knowledge: {
    list: () => request(`${UCORE_API}/api/knowledge`),
    search: (query: string) => request(`${UCORE_API}/api/knowledge/search?q=${encodeURIComponent(query)}`),
    workspaces: () => request(`${UCORE_API}/api/knowledge/workspaces`),
  },
  library: {
    build: () => request(`${UCORE_API}/api/library/build`, { method: 'POST' }),
    search: (query: string, source?: string) => {
      let url = `${UCORE_API}/api/library/search?q=${encodeURIComponent(query)}`
      if (source) url += `&source=${source}`
      return request(url)
    },
    stats: () => request(`${UCORE_API}/api/library/stats`),
  },
  vault: {
    /** Fetch vault layer topology from the plate system */
    topology: () => request(`${UCORE_API}/api/vault/topology`),
    /** Get vault layer details */
    layers: () => request(`${UCORE_API}/api/vault/layers`),
    /** Trigger a vault sync */
    sync: (source?: string) => request(`${UCORE_API}/api/knowledge/sync`, {
      method: 'POST',
      body: JSON.stringify(source ? { source } : {}),
    }),
  },
}

/**
 * @description Ollama local LLM API
 */
export const ollamaApi = {
  baseUrl: OLLAMA_API,
  models: () => request(`${OLLAMA_API}/api/tags`),
}

export const api = {
  snackbar: snackbarApi,
  ucore: ucoreApi,
  ollama: ollamaApi,
}

export default api
