/**
 * @module stores/chat
 * @description Chat state — messages, conversations, model selection, agent mode.
 * Ported from AssistUISurface.tsx local state (React).
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface Conversation {
  id: string
  title: string
  messages: ChatMessage[]
  model: string
  createdAt: string
  updatedAt: string
}

export interface ModelOption {
  id: string
  provider: string
  name: string
}

export type AgentMode = 'vault' | 'developer' | 'agent'

export interface PromptCard {
  id: string
  icon: string
  label: string
  context?: string
}

const SNACKBAR_API = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

function generateId(): string {
  return `conv-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function msgId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`
}

// ─── Persistence ───────────────────────────────────────────────────

function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem('assistui-conversations')
    if (!raw) return []
    return JSON.parse(raw)
  } catch {
    return []
  }
}

function persistConversations(convs: Conversation[]) {
  localStorage.setItem('assistui-conversations', JSON.stringify(convs))
}

// ─── Store ─────────────────────────────────────────────────────────

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<ChatMessage[]>([welcomeMessage()])
  const input = ref('')
  const loading = ref(false)
  const snackbarStatus = ref<'checking' | 'online' | 'offline'>('checking')
  const activeAgent = ref<AgentMode>('vault')
  const prompts = ref<PromptCard[]>(DEFAULT_PROMPTS)
  const models = ref<ModelOption[]>([
    { id: 'llama3.2', provider: 'ollama', name: 'Llama 3.2' },
    { id: 'mistral', provider: 'ollama', name: 'Mistral' },
    { id: 'gpt-4o', provider: 'openrouter', name: 'GPT-4o' },
  ])
  const selectedModel = ref('llama3.2')
  const conversations = ref<Conversation[]>(loadConversations())
  const activeConversation = ref<string | null>(null)

  // Computed
  const hasMessages = computed(() => messages.value.length > 1)
  const currentModelName = computed(
    () => models.value.find(m => m.id === selectedModel.value)?.name || selectedModel.value
  )

  // ─── Actions ───────────────────────────────────────────────────

  function welcomeMessage(): ChatMessage {
    return {
      id: 'welcome',
      role: 'assistant',
      content: `# Hi friend\n\nI'm your OK assistant with streaming MCP protocol, model selection, and agent management.\n\nWhat would you like to do, today?`,
      timestamp: new Date(),
    }
  }

  async function sendMessage(text?: string) {
    const message = (text || input.value).trim()
    if (!message || loading.value) return

    messages.value.push({
      id: msgId('user'),
      role: 'user',
      content: message,
      timestamp: new Date(),
    })
    input.value = ''
    loading.value = true

    const assistantId = msgId('assistant')
    messages.value.push({
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    })

    try {
      // Try streaming via SSE
      const params = new URLSearchParams({ message, agent: activeAgent.value })
      const res = await fetch(`${SNACKBAR_API}/api/chat/stream?${params}`, {
        signal: AbortSignal.timeout(60000),
      })

      if (!res.ok) throw new Error(`API returned ${res.status}`)

      const reader = res.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (!data) continue
            try {
              const parsed = JSON.parse(data)
              if (parsed.token) {
                const msg = messages.value.find(m => m.id === assistantId)
                if (msg) msg.content += parsed.token
              }
            } catch { /* skip malformed */ }
          }
        }
      }
    } catch {
      // Fallback to non-streaming POST
      try {
        const res = await fetch(`${SNACKBAR_API}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message,
            agent: activeAgent.value,
            history: messages.value.map(m => ({ role: m.role, content: m.content })),
          }),
          signal: AbortSignal.timeout(15000),
        })

        if (res.ok) {
          const data = await res.json()
          const msg = messages.value.find(m => m.id === assistantId)
          if (msg) msg.content = data.response || data.message || 'No response received.'
        } else {
          throw new Error(`API returned ${res.status}`)
        }
      } catch {
        const msg = messages.value.find(m => m.id === assistantId)
        if (msg) {
          msg.content = `**Echo:** ${message}\n\n> _AI is offline. Start the snackbar server for AI-powered responses._`
        }
      }
    } finally {
      loading.value = false
    }
  }

  function setActiveAgent(agent: AgentMode) {
    activeAgent.value = agent
    fetchPrompts()
  }

  function setModel(modelId: string) {
    selectedModel.value = modelId
  }

  function clearChat() {
    messages.value = [welcomeMessage()]
    activeConversation.value = null
  }

  function newConversation() {
    saveCurrentConversation()
    clearChat()
  }

  function saveCurrentConversation() {
    if (messages.value.length <= 1) return

    const title = messages.value.find(m => m.role === 'user')?.content.slice(0, 60) || 'New conversation'
    const now = new Date().toISOString()

    if (activeConversation.value) {
      const idx = conversations.value.findIndex(c => c.id === activeConversation.value)
      if (idx !== -1) {
        conversations.value[idx] = {
          ...conversations.value[idx],
          messages: messages.value,
          title,
          model: selectedModel.value,
          updatedAt: now,
        }
      }
    } else {
      const newConv: Conversation = {
        id: generateId(),
        title,
        messages: messages.value,
        model: selectedModel.value,
        createdAt: now,
        updatedAt: now,
      }
      conversations.value.push(newConv)
      activeConversation.value = newConv.id
    }
    persistConversations(conversations.value)
  }

  function loadConversation(convId: string) {
    const conv = conversations.value.find(c => c.id === convId)
    if (!conv) return
    messages.value = conv.messages.map(m => ({ ...m, timestamp: new Date(m.timestamp) }))
    activeConversation.value = convId
  }

  function deleteConversation(convId: string) {
    conversations.value = conversations.value.filter(c => c.id !== convId)
    persistConversations(conversations.value)
    if (activeConversation.value === convId) {
      clearChat()
    }
  }

  async function checkStatus() {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/health`, { signal: AbortSignal.timeout(2000) })
      snackbarStatus.value = res.ok ? 'online' : 'offline'
    } catch {
      snackbarStatus.value = 'offline'
    }
  }

  async function fetchPrompts() {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/chat/prompts?agent=${activeAgent.value}`, {
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data.prompts) && data.prompts.length > 0) {
          const valid = data.prompts.filter((p: any) => p.id && p.label && p.icon)
          if (valid.length > 0) prompts.value = valid
        }
      }
    } catch { /* keep defaults */ }
  }

  async function fetchModels() {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/models`, { signal: AbortSignal.timeout(3000) })
      if (res.ok) {
        const data = await res.json()
        if (data.models?.length > 0) models.value = data.models
      }
    } catch { /* keep defaults */ }
  }

  return {
    // State
    messages,
    input,
    loading,
    snackbarStatus,
    activeAgent,
    prompts,
    models,
    selectedModel,
    conversations,
    activeConversation,
    // Computed
    hasMessages,
    currentModelName,
    // Actions
    sendMessage,
    setActiveAgent,
    setModel,
    clearChat,
    newConversation,
    saveCurrentConversation,
    loadConversation,
    deleteConversation,
    checkStatus,
    fetchPrompts,
    fetchModels,
    welcomeMessage,
  }
})

// ─── Constants ─────────────────────────────────────────────────────

const DEFAULT_PROMPTS: PromptCard[] = [
  { id: 'resume', icon: 'edit_note', label: 'Pick up where you left off', context: 'Continue your last project' },
  { id: 'new-project', icon: 'add', label: 'Start a new project', context: 'Create from template' },
  { id: 'research', icon: 'search', label: 'Research a topic & compile binder', context: 'Gather and organise' },
  { id: 'review', icon: 'visibility', label: 'Review recent changes', context: 'Check activity log' },
  { id: 'brainstorm', icon: 'bolt', label: 'Brainstorm ideas', context: 'Creative exploration' },
  { id: 'plan', icon: 'format_list_bulleted', label: 'Plan your week', context: 'Schedule & priorities' },
]

export const AGENTS: { id: AgentMode; icon: string; label: string; desc: string }[] = [
  { id: 'vault', icon: 'chat', label: 'Vault', desc: 'User mode — personal docs, projects, knowledge' },
  { id: 'developer', icon: 'code', label: 'Developer', desc: 'Dev mode — code, repos, skills, automation' },
  { id: 'agent', icon: 'smart_toy', label: 'Agent', desc: 'Custom agent builder & configuration' },
]
