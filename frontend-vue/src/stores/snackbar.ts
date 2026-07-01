/**
 * @module stores/snackbar
 * @description Global snackbar notification queue.
 * Connects to backend /api/snacks endpoints for persistent snack delivery.
 * Ported from useSurfaceStore.ts (React) → rebuilt for Vue 3 + Pinia.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface SnackbarItem {
  id: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  duration?: number
  timestamp: number
  source?: string
  status?: 'pending' | 'delivered' | 'failed'
}

const API_BASE = '/api/snacks'

export const useSnackbarStore = defineStore('snackbar', () => {
  const items = ref<SnackbarItem[]>([])
  const maxItems = 5
  const loading = ref(false)
  const error = ref<string | null>(null)

  function show(message: string, type: SnackbarItem['type'] = 'info', duration = 4000, source = 'ui') {
    const item: SnackbarItem = {
      id: crypto.randomUUID(),
      message,
      type,
      duration,
      timestamp: Date.now(),
      source,
      status: 'pending',
    }
    items.value.push(item)
    if (items.value.length > maxItems) {
      items.value.shift()
    }

    // Persist to backend
    fetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: type, message, priority: 'normal', source }),
    })
      .then(res => res.ok ? item.status = 'delivered' : item.status = 'failed')
      .catch(() => { item.status = 'failed' })

    if (duration > 0) {
      setTimeout(() => dismiss(item.id), duration)
    }
  }

  function dismiss(id: string) {
    items.value = items.value.filter(i => i.id !== id)
  }

  function clear() {
    items.value = []
  }

  async function refreshQueue() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}?limit=20`)
      if (res.ok) {
        const data = await res.json()
        // Merge server snacks into local items
        for (const s of data.snacks || []) {
          if (!items.value.find(i => i.id === s.id)) {
            items.value.push({
              id: s.id,
              message: s.message || s.type,
              type: s.type === 'error' ? 'error' : s.type === 'warning' ? 'warning' : 'info',
              duration: 0,
              timestamp: new Date(s.timestamp || Date.now()).getTime(),
              source: s.source || 'backend',
              status: s.status || 'pending',
            })
          }
        }
      }
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  return { items, maxItems, loading, error, show, dismiss, clear, refreshQueue }
})
