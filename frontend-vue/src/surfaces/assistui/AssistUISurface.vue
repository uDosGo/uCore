<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <!-- AssistUI agent tabs (Vault, Developer, Agent) -->
    <SurfaceTabNav
      v-model="activeAgentTab"
      :tabs="ASSISTUI_TABS"
      :show-toggle="false"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content assistui-shell">
      <!-- Top Bar: Model picker + Status + Actions -->
      <div class="surface__topbar">
        <div class="assistui-controls-row">
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
            <button class="usx-button" @click="chat.clearChat()">
              <UIcon name="delete" /> Clear
            </button>
          </div>
        </div>
      </div>

      <!-- Main Content — USX surface__content replaces surface__main + surface__body -->
      <!-- Chat Body — USX surface__messages handles scroll + spacing -->
      <div class="surface__messages">
        <!-- Messages -->
        <div
          v-for="msg in chat.messages"
          :key="msg.id"
          class="surface__message"
          :class="`surface__message--${msg.role}`"
        >
          <div class="surface__message-header">
            <span class="surface__message-role">
              {{ msg.role === 'user' ? 'You' : 'Assistant' }}
            </span>
            <span class="surface__message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
          <div class="surface__message-body" v-html="renderMarkdown(msg.content)" />
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

      <!-- Input — USX surface__footer + surface__input-row -->
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
</template>

<script setup lang="ts">
/**
 * @component AssistUISurface
 * @description Full-page AI chat interface with streaming, model selection, and conversation management.
 * Uses USX surface classes from usx-standard.css.
 * @category surfaces
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useShellStore } from '../../stores/shell'
import UIcon from '../../skills/atoms/UIcon.vue'
import { useChatStore, AGENTS } from '../../stores/chat'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'
import type { TabDef } from '../../skills/molecules/SurfaceTabNav.vue'

const shell = useShellStore()
const chat = useChatStore()

// AssistUI agent tabs — mapped from AGENTS for SurfaceTabNav
const ASSISTUI_TABS: TabDef[] = AGENTS.map(a => ({
  id: a.id,
  label: a.label,
  icon: a.icon,
}))

const activeAgentTab = ref(chat.activeAgent)

// Sync activeAgentTab when chat.activeAgent changes externally
watch(() => chat.activeAgent, (agent) => {
  activeAgentTab.value = agent
})

// Update agent when a tab is clicked
watch(activeAgentTab, (tabId) => {
  if (tabId && tabId !== chat.activeAgent) {
    chat.setActiveAgent(tabId as any)
  }
})

const modelPickerOpen = ref(false)
const messagesEl = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

const statusText = computed(() => {
  switch (chat.snackbarStatus) {
    case 'online': return 'AI Online'
    case 'checking': return 'Connecting...'
    default: return 'AI Offline'
  }
})

const formatTime = (timestamp: Date) => {
  return new Intl.DateTimeFormat('en', { hour: 'numeric', minute: '2-digit' }).format(timestamp)
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

/* ─── Nav-link styled buttons in topbar (model picker + New/Clear) ─── */
.assistui-model-section .usx-button,
.assistui-status-bar .usx-button {
  border: none;
  background: transparent;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  transition: color var(--usx-transition-fast), background var(--usx-transition-fast);
}

.assistui-model-section .usx-button:hover,
.assistui-status-bar .usx-button:hover {
  border: none;
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.assistui-model-section .usx-button:active,
.assistui-status-bar .usx-button:active,
.assistui-model-section .usx-button:focus,
.assistui-status-bar .usx-button:focus {
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface);
  box-shadow: none;
  outline: none;
}

/* Remove global focus-visible outline for AssistUI elements — they have their own focus styling */
.assistui-model-section .usx-button:focus-visible,
.assistui-status-bar .usx-button:focus-visible,
.assistui-input:focus-visible,
.assistui-submit-btn:focus-visible {
  outline: none;
}

/* Also suppress the global .usx-button:active background on nav-link styled buttons */
.assistui-model-section .usx-button:active,
.assistui-status-bar .usx-button:active {
  background: transparent;
  box-shadow: none;
}

.assistui-controls-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  width: 100%;
}

.assistui-shell {
  max-width: none;
  width: 100%;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
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
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  min-width: var(--usx-sidebar-width);
  z-index: 10;
  box-shadow: 0 var(--usx-spacing-xs) var(--usx-spacing-md) rgba(0, 0, 0, 0.15);
}

.assistui-model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: transparent;
  color: var(--usx-color-on-surface);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  transition: background 0.15s ease;
  text-align: left;
}

.assistui-model-option:hover {
  background: var(--usx-color-surface-hover);
}

.assistui-model-option--active {
  background: var(--usx-color-surface-active);
  color: var(--usx-color-primary);
}

.assistui-model-provider {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
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
  width: var(--usx-spacing-sm);
  height: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-on-surface-muted);
  transition: background 0.3s ease;
}

.assistui-status-dot--online {
  background: var(--usx-color-success);
}

.assistui-status-text {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.assistui-status-sep {
  width: var(--usx-border-width);
  height: calc(var(--usx-spacing-lg) - var(--usx-spacing-xs));
  background: var(--usx-color-border);
}

/* Messages use USX .surface__messages / .surface__message from usx-standard.css.
   Extend with custom header/metadata styling. */
.surface__messages {
  padding: var(--usx-spacing-xl) var(--usx-spacing-lg);
}

.surface__message {
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
}

.surface__message--user {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  margin-left: auto;
  max-width: 80%;
}

.surface__message--assistant {
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  margin-right: auto;
  max-width: 100%;
}

.surface__message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
}

.assistui-message-role {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-primary);
}

.assistui-message-time {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.assistui-message-body {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
  line-height: var(--usx-line-height-relaxed);
}

.assistui-message-body h1,
.assistui-message-body h2,
.assistui-message-body h3 {
  margin: var(--usx-spacing-md) 0 var(--usx-spacing-sm);
}

.assistui-message-body code {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-sm);
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-primary);
}

.assistui-prompt-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16ch, 1fr));
  gap: var(--usx-spacing-lg);
  margin: var(--usx-spacing-lg) 0;
  padding: var(--usx-spacing-lg) 0;
}

.assistui-prompt-card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  align-items: center;
  text-align: center;
  padding: var(--usx-spacing-lg);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  cursor: pointer;
  transition: all var(--usx-transition-base, 0.15s ease);
  color: var(--usx-color-on-surface);
}



.assistui-prompt-card:hover {
  background: var(--usx-color-surface-hover);
  border-color: var(--usx-color-primary);
  transform: translateY(calc(var(--usx-spacing-1) * -1));
  box-shadow: 0 var(--usx-spacing-sm) var(--usx-spacing-lg) rgba(0, 0, 0, 0.08);
}

.assistui-prompt-card-label {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}

.assistui-prompt-card-context {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.assistui-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
}

.assistui-loading-dot {
  width: var(--usx-spacing-sm);
  height: var(--usx-spacing-sm);
  border-radius: 50%;
  background: var(--usx-color-primary);
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

/* ─── Input & Submit ────────────────────────────────────────────── */
.assistui-input {
  flex: 1;
  min-height: var(--usx-touch-min);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-family: var(--usx-font-family-sans);
  font-size: var(--usx-font-size-base);
  resize: vertical;
  outline: none;
}

.assistui-input:focus {
  border-color: var(--usx-color-primary);
}

.assistui-submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  padding: 0;
  border: none;
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  cursor: pointer;
  font-size: var(--usx-font-size-lg);
  transition: background var(--usx-transition-fast), transform var(--usx-transition-fast);
  flex-shrink: 0;
}

.assistui-submit-btn:hover {
  background: var(--usx-color-primary-hover);
  transform: scale(1.05);
}

.assistui-submit-btn:active {
  transform: scale(0.95);
}
</style>
