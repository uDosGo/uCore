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
  createBuffer,
  writeString,
  scroll as scrollBuffer,
  type GridUICanvasElement,
} from '../../vendor/gridui-canvas'

const cols = 80
const rows = 24
const gridContainer = ref<HTMLDivElement>()
const cmdInput = ref<HTMLInputElement>()
const command = ref('')
let gridEl: GridUICanvasElement | null = null
let cursorY = 0

onMounted(() => {
  if (!gridContainer.value) return
  gridEl = createGridUICanvas({ cols, rows, font: 'pressstart2p', cellSize: 16 })
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
  printLine('GridUI Canvas Engine -- Framework-Agnostic Web Component', 2, 0)
  printLine('Type "HELP" for commands, "DEMO" for a demo.', 7, 0)
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
  printLine('  Grid Buffer: 80x24 cells', 2, 0)
  printLine('  Rendering:   CSS Grid of <span> elements', 2, 0)
  printLine('  Engine:      grid-algebra (pure TypeScript)', 2, 0)
  printLine('  Component:   <gridui-canvas> Web Component', 2, 0)
  printLine('  Framework:   None (framework-agnostic)', 5, 0)
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
  overflow: auto;
  padding: var(--usx-spacing-sm);
}

.terminal-prompt {
  color: #238636;
  font-family: monospace;
  font-weight: bold;
}

.terminal-input {
  flex: 1;
  background: var(--pico-background-color);
  color: var(--pico-color);
  border-radius: var(--usx-border-radius-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-family: monospace;
  font-size: var(--usx-font-size-sm);
  outline: none;
}

.terminal-input:focus {
  border-color: #58a6ff;
}

.terminal-info {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  font-family: monospace;
}
</style>
