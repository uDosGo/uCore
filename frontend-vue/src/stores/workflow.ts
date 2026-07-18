/**
 * @module stores/workflow
 * @description Workflow surface state — tasks, missions, binder, publish, kanban.
 * Wires to backend /api/workflows/*, /api/system/workflow, /api/workflow/tasks,
 * and /api/knowledge/adapter/mission-task-binder endpoints.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type WorkflowTab = 'mission-control' | 'tasks' | 'binder' | 'editor' | 'publish'

export interface WorkflowTask {
  id: string
  title: string
  status: string
  priority: 'low' | 'medium' | 'high'
  board: string
  tags: string[]
  description: string
}

export interface WorkflowFile {
  id: string
  path: string
  filename: string
  extension: string
  binder: string
  content: string
  readOnly: boolean
}

export interface Mission {
  id: string
  title: string
  status: string
  priority: string
  description: string
  taskIds: string[]
}

export interface MissionTaskBinderRow {
  workspace_id: string
  mission: string
  task: string
  binder: string
  title: string
}

export interface WorkflowDefinition {
  id: string
  name: string
  description: string
  schedule: string
  steps: Array<{ type: string; skill_id: string; params: Record<string, unknown> }>
  created_at: string
  updated_at: string
}

export interface WorkflowRun {
  run_id: string
  workflow_id: string
  workflow_name: string
  started_at: string
  finished_at: string
  status: string
  steps: Array<{
    index: number
    type: string
    skill_id: string
    success: boolean
    result?: Record<string, unknown>
    error?: string
  }>
}

export interface WorkflowStatus {
  domain?: string
  source_of_truth?: string
  next_actions?: string[]
  tasker?: {
    boards: Array<{ name: string; count: number; path: string }>
    total_tasks: number
  }
  vault?: {
    ready: boolean
    missing_layers: string[]
  }
  appflowy?: {
    status: string
    mode: string
    enabled_by_default: boolean
    available: boolean
    database_count: number
    workspace_count: number
    errors: string[]
  }
  maintenance?: {
    scheduler_status: string
    next_run: string
  }
}

export const WORKFLOW_TABS: { id: WorkflowTab; label: string; icon: string }[] = [
  { id: 'mission-control', label: 'Mission Control', icon: 'dashboard' },
  { id: 'binder', label: 'Binder', icon: 'folder' },
  { id: 'tasks', label: 'Tasks', icon: 'task' },
  { id: 'editor', label: 'Editor', icon: 'article' },
  { id: 'publish', label: 'Publish', icon: 'publish' },
]

const API = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

const SAMPLE_TASKS: WorkflowTask[] = [
  { id: 'seed-1', title: 'Plan the week', status: 'in-progress', priority: 'high', board: 'planning', tags: ['planning', 'weekly'], description: 'Review goals and lock top priorities for the week.' },
  { id: 'seed-2', title: 'Draft article outline', status: 'todo', priority: 'medium', board: 'writing', tags: ['writing', 'content'], description: 'Create a clear outline before drafting full sections.' },
  { id: 'seed-3', title: 'Organize life admin docs', status: 'review', priority: 'medium', board: 'admin', tags: ['admin', 'records'], description: 'Collect invoices, reminders, and account documents.' },
  { id: 'seed-4', title: 'Summarize this week learning', status: 'completed', priority: 'low', board: 'learning', tags: ['learning', 'weekly-review'], description: 'Publish a short recap with key ideas and next actions.' },
  { id: 'seed-5', title: 'Schedule health appointments', status: 'todo', priority: 'high', board: 'personal', tags: ['health', 'personal'], description: 'Book pending checkups and note preparation items.' },
  { id: 'seed-6', title: 'Prepare monthly budget review', status: 'blocked', priority: 'medium', board: 'finance', tags: ['finance', 'planning'], description: 'Waiting for final bank export before reconciliation.' },
]

const SAMPLE_MISSIONS: Mission[] = [
  { id: 'm1', title: 'Vue Migration Wave 2', status: 'active', priority: 'high', description: 'Port all secondary surfaces to Vue 3', taskIds: ['1', '2', '3', '4'] },
  { id: 'm2', title: 'Quality & Testing', status: 'active', priority: 'medium', description: 'Add tests, a11y, and performance optimization', taskIds: ['5', '6'] },
  { id: 'm3', title: 'Vue Migration Wave 1', status: 'completed', priority: 'high', description: 'Port core surfaces: Dashboard, AssistUI, Developer, Server', taskIds: ['7', '8'] },
]

export const useWorkflowStore = defineStore('workflow', () => {
  const activeTab = ref<WorkflowTab>('mission-control')
  const tasks = ref<WorkflowTask[]>(SAMPLE_TASKS)
  const missions = ref<Mission[]>(SAMPLE_MISSIONS)
  const selectedTask = ref<WorkflowTask | null>(null)
  const selectedFile = ref<WorkflowFile | null>(null)
  const editorOpen = ref(false)
  const showEditorPane = ref(false)
  const paneLayout = ref<'split' | 'stacked'>('stacked')

  // Backend-fetched state
  const loading = ref(false)
  const error = ref<string | null>(null)
  const workflowStatus = ref<WorkflowStatus | null>(null)
  const missionTaskBinderRows = ref<MissionTaskBinderRow[]>([])
  const workflowDefinitions = ref<WorkflowDefinition[]>([])
  const workflowRuns = ref<WorkflowRun[]>([])

  function setTab(tab: WorkflowTab) {
    activeTab.value = tab
  }

  const tasksByStatus = computed(() => {
    const groups: Record<string, WorkflowTask[]> = { todo: [], 'in-progress': [], review: [], blocked: [], completed: [] }
    for (const t of tasks.value) {
      if (!groups[t.status]) groups[t.status] = []
      groups[t.status].push(t)
    }
    return groups
  })

  const totalTasks = computed(() => tasks.value.length)
  const inProgressCount = computed(() => tasks.value.filter(t => t.status === 'in-progress').length)
  const completedCount = computed(() => tasks.value.filter(t => t.status === 'completed').length)

  /** Fetch overall workflow status from user endpoint with legacy fallback */
  async function fetchWorkflowStatus(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      let res = await fetch(`${API}/api/user/workflow/status`, {
        signal: AbortSignal.timeout(8000),
      })
      if (res.status === 404) {
        res = await fetch(`${API}/api/system/workflow`, {
          signal: AbortSignal.timeout(8000),
        })
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      workflowStatus.value = data
      // Populate tasks from tasker boards if available
      if (data.tasker?.boards) {
        // Merge counts into missions for now
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch workflow status'
      console.warn('Workflow status fetch failed, using sample data', e)
    } finally {
      loading.value = false
    }
  }

  /** Fetch tasks from backend /api/workflow/tasks */
  async function fetchTasks(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API}/api/workflow/tasks?scope=user`, {
        signal: AbortSignal.timeout(8000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (Array.isArray(data.tasks)) {
        const mapped = data.tasks.map((t: any) => ({
          id: t.id || t.source_id || '',
          title: t.title || 'Untitled',
          status: t.status || 'todo',
          priority: t.priority || 'medium',
          board: t.board || 'general',
          tags: t.tags || [],
          description: t.description || t.summary || '',
        }))
        tasks.value = mapped.length > 0 ? mapped : [...SAMPLE_TASKS]
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch tasks'
      console.warn('Tasks fetch failed, using sample data', e)
    } finally {
      loading.value = false
    }
  }

  /** Fetch mission/task/binder projections from /api/knowledge/adapter/mission-task-binder */
  async function fetchMissionTaskBinder(workspaceId?: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({ limit: '100' })
      if (workspaceId) params.set('workspace_id', workspaceId)
      const res = await fetch(`${API}/api/knowledge/adapter/mission-task-binder?${params.toString()}`, {
        signal: AbortSignal.timeout(8000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (Array.isArray(data.rows)) {
        missionTaskBinderRows.value = data.rows
        // Build missions from unique mission values
        const missionMap = new Map<string, MissionTaskBinderRow[]>()
        for (const row of data.rows) {
          const key = row.mission || 'Unknown Mission'
          if (!missionMap.has(key)) missionMap.set(key, [])
          missionMap.get(key)!.push(row)
        }
        missions.value = Array.from(missionMap.entries()).map(([title, rows], idx) => ({
          id: `mtb-${idx}`,
          title,
          status: 'active',
          priority: 'medium',
          description: `${rows.length} tasks across ${new Set(rows.map(r => r.binder)).size} binders`,
          taskIds: rows.map(r => r.task),
        }))
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch mission/task binder data'
      console.warn('Mission/task binder fetch failed, using sample data', e)
    } finally {
      loading.value = false
    }
  }

  /** Fetch workflow definitions from /api/workflows */
  async function fetchWorkflowDefinitions(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API}/api/workflows`, {
        signal: AbortSignal.timeout(8000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (Array.isArray(data.workflows)) {
        workflowDefinitions.value = data.workflows
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch workflow definitions'
      console.warn('Workflow definitions fetch failed', e)
    } finally {
      loading.value = false
    }
  }

  /** Fetch recent workflow runs from /api/workflows/runs */
  async function fetchWorkflowRuns(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API}/api/workflows/runs?limit=20`, {
        signal: AbortSignal.timeout(8000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (Array.isArray(data.runs)) {
        workflowRuns.value = data.runs
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch workflow runs'
      console.warn('Workflow runs fetch failed', e)
    } finally {
      loading.value = false
    }
  }

  /** Fetch all data for the current surface at once */
  async function fetchAll(): Promise<void> {
    await Promise.allSettled([
      fetchWorkflowStatus(),
      fetchTasks(),
      fetchMissionTaskBinder(),
      fetchWorkflowDefinitions(),
      fetchWorkflowRuns(),
    ])
  }

  async function archiveUserWorkflow(reason = 'manual'): Promise<unknown> {
    const res = await fetch(`${API}/api/user/workflow/archive`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
      signal: AbortSignal.timeout(30000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  }

  async function resetUserWorkflow(reason = 'reset'): Promise<unknown> {
    const res = await fetch(`${API}/api/user/workflow/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
      signal: AbortSignal.timeout(60000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    await fetchAll()
    return data
  }

  async function seedUserWorkflow(reason = 'seed-only'): Promise<unknown> {
    const res = await fetch(`${API}/api/user/workflow/seed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
      signal: AbortSignal.timeout(30000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    await fetchAll()
    return data
  }

  function selectTask(task: WorkflowTask) {
    selectedFile.value = null
    selectedTask.value = task
    editorOpen.value = true
    // Stay on the tasks tab — editor opens alongside it as a column
  }

  function selectFile(file: WorkflowFile) {
    selectedTask.value = null
    selectedFile.value = {
      ...file,
      binder: file.binder || 'Sandbox',
    }
    editorOpen.value = true
    showEditorPane.value = true
    activeTab.value = 'editor'
  }

  function closeEditor() {
    editorOpen.value = false
    selectedTask.value = null
    selectedFile.value = null
    showEditorPane.value = true
  }

  function updateEditorContent(value: string) {
    if (selectedTask.value) {
      selectedTask.value.description = value
    }
    if (selectedFile.value) {
      selectedFile.value.content = value
    }
  }

  function toggleEditorPane() {
    showEditorPane.value = !showEditorPane.value
  }

  function togglePaneLayout() {
    paneLayout.value = paneLayout.value === 'split' ? 'stacked' : 'split'
  }

  return {
    activeTab,
    tasks,
    missions,
    selectedTask,
    selectedFile,
    editorOpen,
    showEditorPane,
    paneLayout,
    loading,
    error,
    workflowStatus,
    missionTaskBinderRows,
    workflowDefinitions,
    workflowRuns,
    totalTasks,
    inProgressCount,
    completedCount,
    tasksByStatus,
    setTab,
    selectTask,
    selectFile,
    closeEditor,
    updateEditorContent,
    toggleEditorPane,
    togglePaneLayout,
    fetchWorkflowStatus,
    fetchTasks,
    fetchMissionTaskBinder,
    fetchWorkflowDefinitions,
    fetchWorkflowRuns,
    fetchAll,
    archiveUserWorkflow,
    resetUserWorkflow,
    seedUserWorkflow,
  }
})
