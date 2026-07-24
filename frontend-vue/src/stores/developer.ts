/**
 * @module stores/developer
 * @description Developer surface state — active tab, repos, reviews, models, chat.
 * Ported from DeveloperSurface.tsx (React).
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type DeveloperTab =
  | 'control' | 'agents' | 'skills' | 'history' | 'workflows'
  | 'repos' | 'review' | 'settings' | 'mcp-servers'

export type DeveloperLane = 'ecosystem' | 'project'

export interface LaneConfig {
  id: DeveloperLane
  label: string
  icon: string
  description: string
  workspace: string
  guardrails: 'confirm_destructive' | 'standard'
}

export interface RepoInfo {
  name: string
  path: string
  branch: string
  status: 'clean' | 'modified'
  changes: number
  remote: string
}

export interface ReviewEntry {
  file: string
  status: 'modified' | 'added' | 'deleted'
  lines: number
  summary: string
}

export interface ProjectRepoOption {
  id: string
  name: string
  path: string
}

export const DEVELOPER_TABS: { id: DeveloperTab; label: string; icon: string }[] = [
  { id: 'control', label: 'Control', icon: 'dashboard' },
  { id: 'agents', label: 'Agents', icon: 'group' },
  { id: 'skills', label: 'Skills', icon: 'extension' },
  { id: 'history', label: 'History', icon: 'history' },
  { id: 'workflows', label: 'Flow', icon: 'account_tree' },
  { id: 'repos', label: 'Repos', icon: 'folder' },
  { id: 'review', label: 'Review', icon: 'visibility' },
  { id: 'settings', label: 'Settings', icon: 'settings' },
  { id: 'mcp-servers', label: 'MCP', icon: 'dns' },
]

const SNACKBAR_API = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

export const DEVELOPER_LANES: LaneConfig[] = [
  {
    id: 'ecosystem',
    label: 'System',
    icon: 'engineering',
    description: 'Working on uCore and uCode with protection guardrails',
    workspace: '~/Code/uCore',
    guardrails: 'confirm_destructive',
  },
  {
    id: 'project',
    label: 'Project',
    icon: 'rocket_launch',
    description: 'Working in non-system repositories under ~/Code',
    workspace: '~/Code',
    guardrails: 'standard',
  },
]

const SYSTEM_REPO_NAMES = new Set(['uCore', 'uCode', 'uServer', 'uConnect', 'uVector'])

export const useDeveloperStore = defineStore('developer', () => {
  const activeTab = ref<DeveloperTab>('control')
  const activeLane = ref<DeveloperLane>('ecosystem')
  const activeProjectRepo = ref<string>('')
  const projectRepos = ref<ProjectRepoOption[]>([])
  const repos = ref<RepoInfo[]>(SAMPLE_REPOS)
  const reviews = ref<ReviewEntry[]>(SAMPLE_REVIEWS)
  const loading = ref(false)
  const activeRepo = ref<string | null>(null)

  // Chat state
  const chatMessages = ref<Array<{ role: string; content: string }>>([])
  const chatLoading = ref(false)

  function setTab(tab: DeveloperTab) {
    activeTab.value = tab
  }

  async function refreshProjectRepos() {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/developer/repos`, {
        signal: AbortSignal.timeout(5000),
      })
      if (!res.ok) return
      const payload = await res.json()
      const list = Array.isArray(payload?.repos) ? payload.repos : []
      projectRepos.value = list
        .filter((repo: any) => {
          const name = String(repo?.name ?? '')
          return !!name && !SYSTEM_REPO_NAMES.has(name)
        })
        .map((repo: any) => ({
          id: String(repo.id ?? repo.name),
          name: String(repo.name ?? repo.id ?? 'unknown'),
          path: String(repo.path ?? ''),
        }))

      if (projectRepos.value.length > 0) {
        const stillValid = projectRepos.value.some((repo) => repo.id === activeProjectRepo.value)
        if (!stillValid) {
          activeProjectRepo.value = projectRepos.value[0].id
          localStorage.setItem('ucore-dev-project-repo', activeProjectRepo.value)
        }
      }
    } catch {
      // Non-fatal: retain cached/default state.
    }
  }

  function workspaceForLane(lane: DeveloperLane): string {
    if (lane === 'ecosystem') {
      return '~/Code/uCore'
    }
    const selected = projectRepos.value.find((repo) => repo.id === activeProjectRepo.value)
    return selected?.path || '~/Code'
  }

  function setLane(lane: DeveloperLane) {
    activeLane.value = lane
    // Persist preference
    localStorage.setItem('ucore-dev-lane', lane)
    if (lane === 'project' && projectRepos.value.length === 0) {
      void refreshProjectRepos()
    }
    // Notify backend of workspace change
    const workspace = workspaceForLane(lane)
    fetch(`${SNACKBAR_API}/api/developer/workspace`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace, lane, repo: activeProjectRepo.value || null }),
    }).catch(() => { /* non-critical */ })
  }

  function setProjectRepo(repoId: string) {
    activeProjectRepo.value = repoId
    localStorage.setItem('ucore-dev-project-repo', repoId)

    if (activeLane.value !== 'project') return

    const workspace = workspaceForLane('project')
    fetch(`${SNACKBAR_API}/api/developer/workspace`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace, lane: 'project', repo: repoId }),
    }).catch(() => { /* non-critical */ })
  }

  const currentLane = computed(() =>
    DEVELOPER_LANES.find((l) => l.id === activeLane.value) ?? DEVELOPER_LANES[0],
  )

  const selectedProjectRepo = computed(() =>
    projectRepos.value.find((repo) => repo.id === activeProjectRepo.value) ?? null,
  )

  const currentWorkspace = computed(() => workspaceForLane(activeLane.value))

  const isEcosystemMode = computed(() => activeLane.value === 'ecosystem')

  async function browseRepo(repoName: string) {
    activeRepo.value = repoName
    loading.value = true
    // TODO: Wire to actual repo browsing API
    setTimeout(() => { loading.value = false }, 500)
  }

  async function sendChatMessage(message: string) {
    chatMessages.value.push({ role: 'user', content: message })
    chatLoading.value = true

    try {
      const res = await fetch(`${SNACKBAR_API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history: chatMessages.value }),
        signal: AbortSignal.timeout(10000),
      })
      const data = await res.json()
      chatMessages.value.push({ role: 'assistant', content: data.response || 'No response' })
    } catch {
      chatMessages.value.push({
        role: 'assistant',
        content: `🤖 **Developer Mode** — Snackbar offline.\n\n> Received: "${message}"\n\n**Quick commands:**\n- \`/review\` — Code review\n- \`/status\` — Repo status\n- \`/skills\` — List skills\n- \`/deploy\` — Deploy service`,
      })
    } finally {
      chatLoading.value = false
    }
  }

  // Restore lane preference on store creation
  const savedLane = localStorage.getItem('ucore-dev-lane')
  if (savedLane === 'ecosystem' || savedLane === 'project') {
    activeLane.value = savedLane
  }

  const savedProjectRepo = localStorage.getItem('ucore-dev-project-repo')
  if (savedProjectRepo) {
    activeProjectRepo.value = savedProjectRepo
  }

  void refreshProjectRepos()

  return {
    activeTab,
    activeLane,
    activeProjectRepo,
    projectRepos,
    currentLane,
    currentWorkspace,
    selectedProjectRepo,
    isEcosystemMode,
    repos,
    reviews,
    loading,
    activeRepo,
    chatMessages,
    chatLoading,
    setTab,
    setLane,
    setProjectRepo,
    refreshProjectRepos,
    browseRepo,
    sendChatMessage,
  }
})

const SAMPLE_REPOS: RepoInfo[] = [
  { name: 'uCore', path: '~/Code/uCore', branch: 'main', status: 'modified', changes: 5, remote: 'origin: git@github.com:uDosGo/uCore.git' },
  { name: 'uConnect', path: '~/Code/uConnect', branch: 'main', status: 'modified', changes: 3, remote: 'origin: git@github.com:uDosGo/uConnect.git' },
  { name: 'uServer', path: '~/Code/uServer', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uServer.git' },
  { name: 'uCode', path: '~/Code/uCode', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uCode.git' },
  { name: 'uVector', path: '~/Code/uVector', branch: 'main', status: 'clean', changes: 0, remote: 'origin: git@github.com:uDosGo/uVector.git' },
]

const SAMPLE_REVIEWS: ReviewEntry[] = [
  { file: 'frontend-vue/src/surfaces/assistui/AssistUISurface.vue', status: 'added', lines: 380, summary: 'Full Vue 3 port of AssistUI chat surface with streaming, agents, models' },
  { file: 'frontend-vue/src/stores/chat.ts', status: 'added', lines: 220, summary: 'Pinia store for chat state, SSE streaming, conversation persistence' },
  { file: 'frontend-vue/src/composables/useMarkdown.ts', status: 'added', lines: 95, summary: 'Lightweight markdown-to-HTML renderer for chat messages' },
  { file: 'frontend/src/surfaces/assistui/AssistUISurface.tsx', status: 'modified', lines: 245, summary: 'React source — tagged for archival after Vue port' },
  { file: 'docs/VUE_REFACTOR_SURFACE_TAGGING.md', status: 'added', lines: 350, summary: 'Canonical surface inventory and migration wave plan' },
]
