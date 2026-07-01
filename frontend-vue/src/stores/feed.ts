/**
 * @module stores/feed
 * @description Feed Store — unified incoming data layer for user activity.
 * Synced with backend /api/feed/* endpoints.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface FeedActivity {
  id: number
  source: string
  type: string
  title: string
  content: string
  url: string
  contact_id: number | null
  context_id: number | null
  timestamp: string
  importance: number
  processed: boolean
  metadata?: Record<string, unknown>
}

export interface BinderSuggestion {
  name: string
  description: string
  confidence: number
  source: string
  activity_count: number
  sample_titles: string[]
}

export interface FeedIngestPayload {
  source: string
  type: string
  title?: string
  content?: string
  url?: string
  contact_name?: string
  importance?: number
}

export type SourceFilter =
  | 'all'
  | 'browser'
  | 'email'
  | 'message'
  | 'alert'
  | 'search'

const API_BASE = 'http://localhost:8484'

async function apiGet(path: string): Promise<any> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`)
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

export const useFeedStore = defineStore('feed', () => {
  const activities = ref<FeedActivity[]>([])
  const suggestions = ref<BinderSuggestion[]>([])
  const sourceFilter = ref<SourceFilter>('all')
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ── Fetch Activities ──────────────────────────────────────

  async function fetchActivities(
    opts: {
      source?: string
      since?: string
      limit?: number
      importanceMin?: number
    } = {},
  ): Promise<FeedActivity[]> {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      const src = opts.source || sourceFilter.value
      if (src && src !== 'all') params.set('source', src)
      if (opts.since) params.set('since', opts.since)
      params.set('limit', String(opts.limit || 50))
      if (opts.importanceMin !== undefined)
        params.set('importance_min', String(opts.importanceMin))

      const data = await apiGet(`/api/feed/query?${params.toString()}`)
      activities.value = data.activities || data || []
      return activities.value
    } catch (e: any) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  // ── Ingest Activity ───────────────────────────────────────

  async function ingestActivity(
    payload: FeedIngestPayload,
  ): Promise<{ id: number; message: string } | null> {
    loading.value = true
    error.value = null
    try {
      const data = await apiPost('/api/feed/ingest', payload)
      return data
    } catch (e: any) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  // ── Fetch Suggestions ─────────────────────────────────────

  async function fetchSuggestions(
    minConfidence: number = 0.5,
  ): Promise<BinderSuggestion[]> {
    loading.value = true
    error.value = null
    try {
      const data = await apiGet(
        `/api/feed/suggest?min_confidence=${minConfidence}`,
      )
      suggestions.value = data.suggestions || data || []
      return suggestions.value
    } catch (e: any) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  // ── Link to Task ──────────────────────────────────────────

  async function linkToTask(
    taskId: string,
    activityId: number,
    linkType: string = 'source',
  ): Promise<{ message: string } | null> {
    try {
      const data = await apiPost('/api/feed/link', {
        task_id: taskId,
        activity_id: activityId,
        link_type: linkType,
      })
      // Refresh activities after linking
      await fetchActivities()
      return data
    } catch (e: any) {
      error.value = e.message
      return null
    }
  }

  // ── Computed ──────────────────────────────────────────────

  const filteredActivities = computed(() => {
    if (sourceFilter.value === 'all') return activities.value
    return activities.value.filter((a) => a.source === sourceFilter.value)
  })

  const pendingSuggestions = computed(() =>
    suggestions.value.filter((s) => s.confidence >= 0.5),
  )

  const sourceIcon = (source: string): string => {
    const icons: Record<string, string> = {
      browser: 'globe',
      email: 'mail',
      message: 'message-circle',
      alert: 'bell',
      search: 'search',
    }
    return icons[source] || 'activity'
  }

  const importanceColor = (importance: number): string => {
    if (importance > 0.8) return '#f85149'
    if (importance > 0.5) return '#d29922'
    return '#3fb950'
  }

  function setSourceFilter(filter: SourceFilter): void {
    sourceFilter.value = filter
    fetchActivities()
  }

  return {
    activities,
    suggestions,
    sourceFilter,
    loading,
    error,
    fetchActivities,
    ingestActivity,
    fetchSuggestions,
    linkToTask,
    filteredActivities,
    pendingSuggestions,
    sourceIcon,
    importanceColor,
    setSourceFilter,
  }
})