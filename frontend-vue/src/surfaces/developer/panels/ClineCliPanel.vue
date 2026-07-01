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
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  font-family: var(--font-mono);
  font-size: 0.9rem;
}

.command-input {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.prompt {
  color: var(--primary);
  font-weight: bold;
}

.command-input input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  font-family: var(--font-mono);
  outline: none;
}

.command-input input:focus {
  border-color: var(--primary);
}

.command-output {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.5rem;
  background: var(--surface-2);
  font-family: var(--font-mono);
}

.command-entry {
  margin-bottom: 1rem;
}

.command-line {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.25rem;
}

.command-text {
  color: var(--text);
}

.result-line {
  padding: 0.5rem;
  border-radius: 4px;
  white-space: pre-wrap;
}

.success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
}

.error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}
</style>