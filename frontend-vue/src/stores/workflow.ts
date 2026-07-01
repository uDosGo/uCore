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
  tasker?: {
    boards: Array<{ name: string; count: number; path: string }>
    total_tasks: number
  }
  maintenance?: {
    scheduler_status: string
    next_run: string
  }
}

export const WORKFLOW_TABS: { id: WorkflowTab; label: string; icon: string }[] = [
  { id: 'mission-control', label: 'Missions', icon: 'dashboard' },
  { id: 'binder', label: 'Binder', icon: 'folder' },
  { id: 'tasks', label: 'Tasks', icon: 'task' },
  { id: 'editor', label: 'Editor', icon: 'article' },
  { id: 'publish', label: 'Publish', icon: 'publish' },
]

const API = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

const SAMPLE_TASKS: WorkflowTask[] = [
  { id: '1', title: 'Port Workflow surface to Vue', status: 'in-progress', priority: 'high', board: 'active', tags: ['vue', 'migration'], description: 'Port the Workflow surface from React to Vue 3' },
  { id: '2', title: 'Port System surface to Vue', status: 'todo', priority: 'high', board: 'active', tags: ['vue', 'migration'], description: 'Port the System admin surface from React to Vue 3' },
  { id: '3', title: 'Port SnackMachine to Vue', status: 'todo', priority: 'medium', board: 'active', tags: ['vue', 'migration'], description: 'Port the SnackMachine surface from React to Vue 3' },
  { id: '4', title: 'Port UCode/GridCore to Vue', status: 'todo', priority: 'medium', board: 'active', tags: ['vue', 'migration'], description: 'Port the UCode GridCore surface from React to Vue 3' },
  { id: '5', title: 'Write Vitest unit tests', status: 'todo', priority: 'medium', board: 'backlog', tags: ['testing'], description: 'Add unit tests for all Skills components' },
  { id: '6', title: 'Accessibility audit', status: 'todo', priority: 'low', board: 'backlog', tags: ['a11y'], description: 'Audit all surfaces for WCAG compliance' },
  { id: '7', title: 'Vue foundation scaffold', status: 'completed', priority: 'high', board: 'active', tags: ['vue', 'foundation'], description: 'Scaffold Vue 3 + Vite + Pinia project' },
  { id: '8', title: 'AssistUI chat surface', status: 'completed', priority: 'high', board: 'active', tags: ['vue', 'assistui'], description: 'Port AssistUI with streaming chat, agents, models' },
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
  const editorOpen = ref(false)
  const showEditorPane = ref(false)
  const paneLayout = ref<'split' | 'stacked'>('split')

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

  /** Fetch overall workflow status from /api/system/workflow */
  async function fetchWorkflowStatus(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API}/api/system/workflow`, {
        signal: AbortSignal.timeout(8000),
      })
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
      const res = await fetch(`${API}/api/workflow/tasks`, {
        signal: AbortSignal.timeout(8000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (Array.isArray(data.tasks)) {
        tasks.value = data.tasks.map((t: any) => ({
          id: t.id || t.source_id || '',
          title: t.title || 'Untitled',
          status: t.status || 'todo',
          priority: t.priority || 'medium',
          board: t.board || 'general',
          tags: t.tags || [],
          description: t.description || t.summary || '',
        }))
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch tasks'
      console.warn('Tasks fetch failed, using sample data', e)
    } finally {
      loading.value = false
    }
  }

  /** Fetch mission/task/binder projections from /api/knowledge/adapter/mission-task-binder */
  async function fetchMissionTaskBinder(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API}/api/knowledge/adapter/mission-task-binder?limit=100`, {
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

  function selectTask(task: WorkflowTask) {
    selectedTask.value = task
    editorOpen.value = true
    // Stay on the tasks tab — editor opens alongside it as a column
  }

  function closeEditor() {
    editorOpen.value = false
    selectedTask.value = null
    showEditorPane.value = true
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
    closeEditor,
    toggleEditorPane,
    togglePaneLayout,
    fetchWorkflowStatus,
    fetchTasks,
    fetchMissionTaskBinder,
    fetchWorkflowDefinitions,
    fetchWorkflowRuns,
    fetchAll,
  }
})
