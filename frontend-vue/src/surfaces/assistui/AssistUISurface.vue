<template>
  <div class="surface">
    <!-- Top Bar: Agent + Model + Status + Actions -->
    <div class="surface__topbar">
      <div class="surface__topbar-inner">
        <!-- Agent pills -->
        <div class="assistui-agent-bar">
          <button
            v-for="agent in AGENTS"
            :key="agent.id"
            class="surface__tab"
            :class="{ 'surface__tab--active': chat.activeAgent === agent.id }"
            :title="agent.desc"
            @click="chat.setActiveAgent(agent.id)"
          >
            <UIcon :name="agent.icon" />
            <span>{{ agent.label }}</span>
          </button>
        </div>

        <!-- Model picker -->
        <div class="assistui-model-section" ref="modelSectionRef">
          <button class="usx-button" @click="modelPickerOpen = !modelPickerOpen">
            <UIcon name="smart_toy" />
            <span>{{ chat.currentModelName }}</span>
            <UIcon name="expand_more" />
          </button>
          <div v-if="modelPickerOpen" class="assistui-model-dropdown">
            <button
              v-for="model in chat.models"
              :key="model.id"
              class="assistui-model-option"
              :class="{ 'assistui-model-option--active': chat.selectedModel === model.id }"
              @click="chat.setModel(model.id); modelPickerOpen = false"
            >
              <span class="assistui-model-provider">{{ model.provider }}</span>
              <span class="assistui-model-name">{{ model.name }}</span>
              <UIcon v-if="chat.selectedModel === model.id" name="check" />
            </button>
          </div>
        </div>

        <!-- Status + Actions -->
        <div class="assistui-status-bar">
          <span
            class="assistui-status-dot"
            :class="{ 'assistui-status-dot--online': chat.snackbarStatus === 'online' }"
          />
          <span class="assistui-status-text">
            {{ statusText }}
          </span>
          <span class="assistui-status-sep" />
          <button class="usx-button" @click="chat.newConversation()">
            <UIcon name="add" /> New
          </button>
          <button class="usx-button" @click="conversationListOpen = !conversationListOpen">
            <UIcon name="history" /> History
          </button>
          <button class="usx-button" @click="chat.clearChat()">
            <UIcon name="delete" /> Clear
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="surface__main">
      <!-- Conversation List Sidebar -->
      <div v-if="conversationListOpen" class="assistui-conv-sidebar">
        <div class="assistui-conv-sidebar-header">
          <h3>Conversations</h3>
          <button class="usx-button-icon" @click="conversationListOpen = false">
            <UIcon name="close" />
          </button>
        </div>
        <div class="assistui-conv-list">
          <div v-if="chat.conversations.length === 0" class="assistui-conv-empty">
            <UIcon name="chat" />
            <span>No saved conversations</span>
          </div>
          <div
            v-for="conv in sortedConversations"
            :key="conv.id"
            class="assistui-conv-item"
            :class="{ 'assistui-conv-item--active': chat.activeConversation === conv.id }"
            @click="chat.loadConversation(conv.id); conversationListOpen = false"
          >
            <div class="assistui-conv-item-info">
              <span class="assistui-conv-item-title">{{ conv.title }}</span>
              <span class="assistui-conv-item-meta">
                {{ conv.messages.length }} messages · {{ formatDate(conv.updatedAt) }}
              </span>
            </div>
            <button
              class="assistui-conv-item-delete"
              @click.stop="chat.deleteConversation(conv.id)"
              title="Delete conversation"
            >
              <UIcon name="close" />
            </button>
          </div>
        </div>
      </div>

      <!-- Chat Body -->
      <div class="surface__body">
        <div class="surface__body-inner">
          <!-- Messages -->
          <div ref="messagesEl" class="assistui-messages">
            <div
              v-for="msg in chat.messages"
              :key="msg.id"
              class="assistui-message"
              :class="`assistui-message--${msg.role}`"
            >
              <div class="assistui-message-header">
                <span class="assistui-message-role">
                  {{ msg.role === 'user' ? 'You' : 'Assistant' }}
                </span>
                <span class="assistui-message-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
              <div class="assistui-message-body" v-html="renderMarkdown(msg.content)" />
            </div>

            <!-- Prompt cards (shown when only welcome message) -->
            <div v-if="chat.prompts.length > 0 && chat.messages.length <= 1" class="assistui-prompt-row">
              <div
                v-for="prompt in chat.prompts"
                :key="prompt.id"
                class="assistui-prompt-card"
                @click="handlePromptClick(prompt)"
              >
                <UIcon :name="resolveIcon(prompt.icon)" />
                <span class="assistui-prompt-card-label">{{ prompt.label }}</span>
                <span v-if="prompt.context" class="assistui-prompt-card-context">{{ prompt.context }}</span>
              </div>
            </div>

            <!-- Loading indicator -->
            <div v-if="chat.loading" class="assistui-loading">
              <span class="assistui-loading-dot" />
              <span class="assistui-loading-dot" />
              <span class="assistui-loading-dot" />
            </div>
          </div>

          <!-- Input -->
          <div class="surface__footer">
            <div class="surface__input-row">
              <textarea
                ref="inputRef"
                v-model="chat.input"
                class="assistui-input"
                placeholder="Ask anything..."
                @keydown="handleInputKeydown"
              />
              <button class="assistui-submit-btn" @click="chat.sendMessage()">
                <UIcon name="send" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component AssistUISurface
 * @description Full-page AI chat interface with streaming, model selection, and conversation management.
 * Uses USX surface classes from usx-standard.css.
 * @category surfaces
 */
import { ref, computed, onMounted } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import { useChatStore, AGENTS } from '../../stores/chat'

const chat = useChatStore()

const modelPickerOpen = ref(false)
const conversationListOpen = ref(false)
const messagesEl = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

const statusText = computed(() => {
  switch (chat.snackbarStatus) {
    case 'online': return 'AI Online'
    case 'checking': return 'Connecting...'
    default: return 'AI Offline'
  }
})

const sortedConversations = computed(() => {
  return [...chat.conversations].sort((a, b) => 
    new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  )
})

const formatTime = (timestamp: Date) => {
  return new Intl.DateTimeFormat('en', { hour: 'numeric', minute: '2-digit' }).format(timestamp)
}

const formatDate = (timestamp: Date | string) => {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(date)
}

const renderMarkdown = (content: string) => {
  return content
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

const resolveIcon = (icon: string) => {
  const emojiMap: Record<string, string> = {
    '⚡': 'bolt',
    '📝': 'edit',
    '🔍': 'search',
    '💡': 'lightbulb',
    '🚀': 'rocket_launch',
  }
  return emojiMap[icon] || icon
}

const handlePromptClick = (prompt: any) => {
  chat.input = prompt.label
  chat.sendMessage()
}

const handleInputKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    chat.sendMessage()
  }
}

onMounted(() => {
  fetch('http://localhost:8484/api/health')
    .then(res => {
      if (res.ok) {
        chat.snackbarStatus = 'online'
      } else {
        chat.snackbarStatus = 'offline'
      }
    })
    .catch(() => {
      chat.snackbarStatus = 'offline'
    })
})
</script>

<style scoped>
/* Surface-specific overrides only — layout handled by .surface__* classes */

.assistui-agent-bar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-wrap: nowrap;
  flex-shrink: 0;
}

.assistui-model-section {
  position: relative;
  flex-shrink: 0;
}

.assistui-model-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: var(--usx-spacing-xs);
  background: var(--pico-card-background-color);
  border-radius: var(--usx-border-radius-md);
  min-width: 200px;
  z-index: 10;
}

.assistui-model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: transparent;
  color: var(--pico-color);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  transition: background 0.15s ease;
  text-align: left;
}

.assistui-model-option:hover {
  background: #1a2332;
}

.assistui-model-option--active {
  background: #1a2332;
  color: var(--pico-primary);
}

.assistui-model-provider {
  font-size: var(--usx-font-size-xs);
  color: var(--pico-muted-color);
}

.assistui-model-name {
  flex: 1;
  margin-left: var(--usx-spacing-sm);
}

.assistui-status-bar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  margin-left: auto;
  flex-shrink: 0;
}

.assistui-status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--usx-border-radius-full);
  background: var(--pico-muted-color);
  transition: background 0.3s ease;
}

.assistui-status-dot--online {
  background: #3fb950;
}

.assistui-status-text {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
}

.assistui-status-sep {
  width: 1px;
  height: 20px;
  background: var(--pico-background-color);
}

.assistui-conv-sidebar {
  width: 280px;
  flex-shrink: 0;
  overflow-y: auto;
  background: var(--pico-card-background-color);
}

.assistui-conv-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-md);
}

.assistui-conv-sidebar-header h3 {
  margin: 0;
  font-size: var(--usx-font-size-base);
  color: var(--pico-color);
}

.assistui-conv-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm);
}

.assistui-conv-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-lg);
  color: var(--pico-muted-color);
  text-align: center;
}

.assistui-conv-item {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-border-radius-md);
  background: var(--pico-background-color);
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
}

.assistui-conv-item:hover {
  background: #1a2332;
}

.assistui-conv-item--active {
  background: #1a2332;
  color: var(--pico-primary);
}

.assistui-conv-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.assistui-conv-item-title {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-color);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.assistui-conv-item-meta {
  font-size: var(--usx-font-size-xs);
  color: var(--pico-muted-color);
}

.assistui-conv-item-delete {
  background: none;
  border: none;
  color: var(--pico-muted-color);
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.assistui-conv-item-delete:hover {
  color: #f85149;
}

.assistui-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-xl) var(--usx-spacing-lg);
  max-width: 100%;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.assistui-input {
  flex: 1;
  min-height: 40px;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-border-radius-lg);
  background: var(--pico-background-color);
  color: var(--pico-color);
  resize: vertical;
}

.assistui-submit-btn {
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg);
  border: none;
  border-radius: var(--usx-border-radius-lg);
  background: var(--pico-primary);
  color: white;
  cursor: pointer;
}

.assistui-submit-btn:hover {
  background: var(--pico-primary-hover);
}

.assistui-message {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-lg);
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-border-radius-md);
  background: var(--pico-background-color);
}

.assistui-message--user {
  background: #1a2332;
  margin-left: auto;
  max-width: 80%;
}

.assistui-message--assistant {
  background: var(--pico-background-color);
  margin-right: auto;
  max-width: 100%;
}

.assistui-message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
}

.assistui-message-role {
  font-size: var(--usx-font-size-sm);
  font-weight: 600;
  color: var(--pico-primary);
}

.assistui-message-time {
  font-size: var(--usx-font-size-xs);
  color: var(--pico-muted-color);
}

.assistui-message-body {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-color);
  line-height: 1.6;
}

.assistui-message-body h1,
.assistui-message-body h2,
.assistui-message-body h3 {
  margin: var(--usx-spacing-md) 0 var(--usx-spacing-sm);
}

.assistui-message-body code {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--usx-border-radius-sm);
  font-family: monospace;
  color: #58a6ff;
}

.assistui-prompt-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--usx-spacing-md);
  margin: var(--usx-spacing-xl) 0;
  padding: var(--usx-spacing-lg) 0;
}

.assistui-prompt-card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  align-items: center;
  text-align: center;
  padding: var(--usx-spacing-lg);
  border-radius: var(--usx-border-radius-lg);
  background: var(--pico-card-background-color);
  border: 1px solid rgba(88, 166, 255, 0.1);
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--pico-color);
}

.assistui-prompt-card:hover {
  background: rgba(88, 166, 255, 0.1);
  border-color: rgba(88, 166, 255, 0.3);
  transform: translateY(-2px);
}

.assistui-prompt-card-label {
  font-size: var(--usx-font-size-sm);
  font-weight: 600;
}

.assistui-prompt-card-context {
  font-size: var(--usx-font-size-xs);
  color: var(--pico-muted-color);
}

.assistui-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
}

.assistui-loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--pico-primary);
  animation: assistui-pulse 1.5s ease-in-out infinite;
}

.assistui-loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.assistui-loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes assistui-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
