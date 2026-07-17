<template>
  <div class="cline-cli-panel">
    <h3>Cline CLI</h3>
    
    <!-- Command Input -->
    <div class="command-input">
      <span class="prompt">$</span>
      <input
        v-model="commandInput"
        @keyup.enter="runCommand"
        placeholder="Enter command..."
        ref="commandInputRef"
      />
    </div>

    <!-- Command Output -->
    <div class="command-output">
      <div v-for="(entry, index) in commandHistory" :key="index" class="command-entry">
        <div class="command-line">
          <span class="prompt">$</span>
          <span class="command-text">{{ entry.command }}</span>
        </div>
        <div class="result-line" :class="entry.success ? 'success' : 'error'">
          {{ entry.result }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ucoreApi, snackbarApi } from '@/api/client'

const commandInput = ref('')
const commandHistory = ref<Array<{command: string, result: string, success: boolean}>>([])
const commandInputRef = ref<HTMLInputElement | null>(null)

const runCommand = async () => {
  if (!commandInput.value.trim()) return
  
  const command = commandInput.value.trim()
  commandHistory.value.push({ command, result: 'Executing...', success: true })
  commandInput.value = ''
  
  try {
    const response = await snackbarApi.exec(command)
    const result = typeof response === 'object' ? JSON.stringify(response, null, 2) : String(response)
    commandHistory.value[commandHistory.value.length - 1].result = result
  } catch (error) {
    commandHistory.value[commandHistory.value.length - 1].result = `Error: ${error}`
    commandHistory.value[commandHistory.value.length - 1].success = false
  }
}

onMounted(() => {
  // Focus the input when component mounts
  if (commandInputRef.value) {
    commandInputRef.value.focus()
  }
})
</script>

<style scoped>
.cline-cli-panel {
  padding: var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
}

.command-input {
  display: flex;
  gap: var(--usx-spacing-sm);
  align-items: center;
}

.prompt {
  color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-bold);
}

.command-input input {
  flex: 1;
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-family: var(--usx-font-family-mono);
  outline: none;
}

.command-input input:focus {
  border-color: var(--usx-color-primary);
}

.command-output {
  flex: 1;
  overflow-y: auto;
  max-height: calc(var(--usx-spacing-2xl) * 12 + var(--usx-spacing-sm));
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  font-family: var(--usx-font-family-mono);
}

.command-entry {
  margin-bottom: var(--usx-spacing-md);
}

.command-line {
  display: flex;
  gap: var(--usx-spacing-sm);
  align-items: center;
  margin-bottom: var(--usx-spacing-xs);
}

.command-text {
  color: var(--usx-color-on-surface);
}

.result-line {
  padding: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  white-space: pre-wrap;
}

.success {
  background: color-mix(in srgb, var(--usx-color-success) 10%, transparent);
  border: var(--usx-border-width) solid color-mix(in srgb, var(--usx-color-success) 30%, transparent);
  color: var(--usx-color-success);
}

.error {
  background: color-mix(in srgb, var(--usx-color-danger) 10%, transparent);
  border: var(--usx-border-width) solid color-mix(in srgb, var(--usx-color-danger) 30%, transparent);
  color: var(--usx-color-danger);
}
</style>