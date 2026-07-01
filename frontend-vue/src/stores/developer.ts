/**
 * @module stores/developer
 * @description Developer surface state — active tab, repos, reviews, models, chat.
 * Ported from DeveloperSurface.tsx (React).
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type DeveloperTab =
  | 'models' | 'agents' | 'kanban' | 'repos' | 'review'
  | 'skills' | 'feed' | 'surfaces' | 'courses' | 'settings' | 'workflows' | 'mcp-servers'

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

export const DEVELOPER_TABS: { id: DeveloperTab; label: string; icon: string }[] = [
  { id: 'models', label: 'Models', icon: 'smart_toy' },
  { id: 'agents', label: 'Dev Agents', icon: 'group' },
  { id: 'kanban', label: 'Kanban', icon: 'view_kanban' },
  { id: 'repos', label: 'Repos', icon: 'folder' },
  { id: 'review', label: 'Review', icon: 'visibility' },
  { id: 'skills', label: 'Skills', icon: 'extension' },
  { id: 'feed', label: 'Feed', icon: 'rss_feed' },
  { id: 'surfaces', label: 'Surfaces', icon: 'dashboard' },
  { id: 'courses', label: 'Courses', icon: 'school' },
  { id: 'workflows', label: 'Dev Flow', icon: 'account_tree' },

  { id: 'mcp-servers', label: 'MCP', icon: 'dns' },
  { id: 'settings', label: 'Settings', icon: 'settings' },
]

const SNACKBAR_API = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

export const useDeveloperStore = defineStore('developer', () => {
  const activeTab = ref<DeveloperTab>('models')
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

  return {
    activeTab,
    repos,
    reviews,
    loading,
    activeRepo,
    chatMessages,
    chatLoading,
    setTab,
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
