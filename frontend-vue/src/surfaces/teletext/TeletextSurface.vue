<template>
  <div class="surface">
    <div class="surface__toolbar">
      <h1 class="surface__topbar-title">Teletext</h1>
      <div class="surface__toolbar-actions">
        <button class="usx-button" @click="loadDemoPage">Demo</button>
        <button class="usx-button" @click="clearGrid">Clear</button>
        <span class="teletext-info">{{ cols }}×{{ rows }}</span>
      </div>
    </div>
    <div class="surface__canvas">
      <div ref="gridContainer" class="teletext-viewport" role="region" aria-label="Teletext page viewer"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @description Teletext surface — Ceefax-style page viewer.
 * Uses the framework-agnostic <gridui-canvas> Web Component.
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { createGridUICanvas, type GridUICanvasElement } from '../../grid-core/gridui-canvas'
import { createBuffer, writeString } from '../../grid-core/index'



const cols = 40
const rows = 25
const gridContainer = ref<HTMLDivElement>()
let gridEl: GridUICanvasElement | null = null

onMounted(() => {
  if (!gridContainer.value) return
  gridEl = createGridUICanvas({ cols, rows, font: 'vt323', cellSize: 20 })
  gridContainer.value.appendChild(gridEl)
  loadDemoPage()
})

onUnmounted(() => {
  gridEl?.remove()
  gridEl = null
})

function loadDemoPage() {
  if (!gridEl) return
  let buf = createBuffer(cols, rows)

  // Header bar
  buf = writeString(buf, 1, 0, 'uDosConnect Teletext', 7, 4, true)
  buf = writeString(buf, 30, 0, 'P100', 7, 4)

  // Separator
  buf = writeString(buf, 0, 1, '='.repeat(cols), 3, 0)

  // Content
  buf = writeString(buf, 2, 3, 'Welcome to uCore Teletext', 7, 0, true)
  buf = writeString(buf, 2, 5, 'GridUI Canvas Engine -- Live', 2, 0)
  buf = writeString(buf, 2, 7, 'Framework-agnostic Web Component', 6, 0)
  buf = writeString(buf, 2, 9, 'Powered by grid-algebra + bbcruntime', 5, 0)

  // Block graphics demo
  buf = writeString(buf, 2, 12, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 4, 0)
  buf = writeString(buf, 2, 13, 'X  Teletext G0 Character Set    X', 4, 0)
  buf = writeString(buf, 2, 14, 'X  Block graphics + mosaic       X', 4, 0)
  buf = writeString(buf, 2, 15, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 4, 0)

  // Footer
  buf = writeString(buf, 0, rows - 2, '='.repeat(cols), 3, 0)
  buf = writeString(buf, 1, rows - 1, 'uDosConnect', 7, 1)
  buf = writeString(buf, 28, rows - 1, 'Page 100', 7, 1)

  gridEl.setBuffer(buf)
}

function clearGrid() {
  gridEl?.clear()
}
</script>

<style scoped>
.teletext-viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 5%;
}

.teletext-viewport gridui-canvas {
  flex-shrink: 0;
}

.teletext-info {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  font-family: monospace;
}
</style>
