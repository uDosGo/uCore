<template>
  <div class="surface">
    <div class="surface__toolbar">
      <h1 class="surface__topbar-title">BBC BASIC Terminal</h1>
      <div class="surface__toolbar-actions">
        <button class="usx-button" @click="clearTerminal">Clear</button>
        <button class="usx-button" @click="runDemo">Demo</button>
        <span class="terminal-info">{{ cols }}×{{ rows }}</span>
      </div>
    </div>
    <div class="surface__canvas">
      <div ref="gridContainer" class="terminal-viewport" role="region" aria-label="Terminal output"></div>
    </div>
    <div class="surface__footer">
      <div class="surface__input-row">
        <span class="terminal-prompt">></span>
        <input
          ref="cmdInput"
          v-model="command"
          class="terminal-input"
          placeholder="Type a command..."
          @keydown.enter="executeCommand"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @description Terminal surface — BBC BASIC terminal emulator.
 * Uses the framework-agnostic <gridui-canvas> Web Component.
 */
import { ref, onMounted, onUnmounted } from 'vue'
import {
  createGridUICanvas,
  type GridUICanvasElement,
} from '../../grid-core/gridui-canvas'
import {
  createBuffer,
  writeString,
  scroll as scrollBuffer,
} from '../../grid-core/index'

const cols = 40
const rows = 25
const gridContainer = ref<HTMLDivElement>()
const cmdInput = ref<HTMLInputElement>()
const command = ref('')
let gridEl: GridUICanvasElement | null = null
let cursorY = 0

onMounted(() => {
  if (!gridContainer.value) return
  gridEl = createGridUICanvas({ cols, rows, font: 'pressstart2p', cellSize: 20 })
  gridContainer.value.appendChild(gridEl)
  printWelcome()
})

onUnmounted(() => {
  gridEl?.remove()
  gridEl = null
})

function printLine(text: string, fg = 7, bg = 0) {
  if (!gridEl) return
  let buf = gridEl.buffer
  if (cursorY >= rows) {
    buf = scrollBuffer(buf, 1)
    cursorY = rows - 1
  }
  buf = writeString(buf, 0, cursorY, text, fg, bg)
  cursorY++
  gridEl.setBuffer(buf)
}

function printWelcome() {
  cursorY = 0
  let buf = createBuffer(cols, rows)
  gridEl?.setBuffer(buf)
  printLine('uDosConnect BBC BASIC Terminal', 4, 0)
  printLine('='.repeat(cols), 3, 0)
  printLine('GridUI Canvas Engine  ·  40x25 Teletext', 2, 0)
  printLine('Type HELP · DEMO · CLEAR · CLS · ABOUT', 7, 0)
  printLine('', 7, 0)
  cursorY = 6
}

function clearTerminal() {
  cursorY = 0
  gridEl?.clear()
}

function runDemo() {
  clearTerminal()
  printLine('uCore GridUI Terminal Demo', 4, 0)
  printLine('', 7, 0)
  printLine('  Grid: 40x25 @20px cells', 2, 0)
  printLine('  Font: pressstart2p + vt323', 2, 0)
  printLine('  Renderer: Canvas 2D', 2, 0)
  printLine('  Scaling: 1x retro base', 5, 0)
  printLine('', 7, 0)
  printLine('  Ready.', 2, 0)
}

function executeCommand() {
  const cmd = command.value.trim()
  command.value = ''
  if (!cmd) return

  printLine(`> ${cmd}`, 6, 0)

  switch (cmd.toUpperCase()) {
    case 'HELP':
      printLine('  Commands: HELP, DEMO, CLEAR, CLS, ABOUT', 2, 0)
      break
    case 'DEMO':
      runDemo()
      break
    case 'CLEAR':
    case 'CLS':
      clearTerminal()
      break
    case 'ABOUT':
      printLine('  uCore GridUI Canvas Engine v1.0', 5, 0)
      printLine('  Framework-agnostic Web Component', 5, 0)
      break
    default:
      printLine(`  Unknown command: ${cmd}`, 1, 0)
  }

  cmdInput.value?.focus()
}
</script>

<style scoped>
.terminal-viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 5%;
}

.terminal-prompt {
  color: var(--usx-color-success);
  font-family: monospace;
  font-weight: bold;
}

.terminal-input {
  flex: 1;
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  border-radius: var(--usx-radius-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-family: monospace;
  font-size: var(--usx-font-size-sm);
  outline: none;
}

.terminal-input:focus {
  border-color: var(--usx-color-primary);
}

.terminal-info {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  font-family: monospace;
}
</style>
