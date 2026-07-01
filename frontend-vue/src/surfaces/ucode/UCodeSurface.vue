<template>
  <div class="surface">
    <div class="surface__toolbar">
      <h1 class="surface__topbar-title">uCode — GridCore</h1>
      <div class="surface__toolbar-actions">
        <button class="usx-button" @click="loadGridDemo">Grid</button>
        <button class="usx-button" @click="loadMapDemo">Map</button>
        <button class="usx-button" @click="clearGrid">Clear</button>
        <span class="ucode-info">{{ cols }}×{{ rows }}</span>
      </div>
    </div>
    <div class="surface__canvas">
      <div ref="gridContainer" class="ucode-viewport" role="region" aria-label="Grid editor viewport"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @description uCode/GridCore surface — grid editor + map view.
 * Uses the framework-agnostic <gridui-canvas> Web Component.
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { createGridUICanvas, type GridUICanvasElement } from '../../grid-core/gridui-canvas'
import { createBuffer, writeString, fill } from '../../grid-core/index'



const cols = 60
const rows = 20
const gridContainer = ref<HTMLDivElement>()
let gridEl: GridUICanvasElement | null = null

onMounted(() => {
  if (!gridContainer.value) return
  gridEl = createGridUICanvas({ cols, rows, font: 'pressstart2p', cellSize: 16 })
  gridContainer.value.appendChild(gridEl)
  loadGridDemo()
})

onUnmounted(() => {
  gridEl?.remove()
  gridEl = null
})

function loadGridDemo() {
  if (!gridEl) return
  let buf = createBuffer(cols, rows)

  // Title
  buf = writeString(buf, 1, 0, 'uCode GridCore -- Grid Editor', 7, 4, true)

  // Grid border
  buf = writeString(buf, 0, 1, '='.repeat(cols), 4, 0)
  for (let y = 2; y < rows - 2; y++) {
    buf = writeString(buf, 0, y, '|', 4, 0)
    buf = writeString(buf, cols - 1, y, '|', 4, 0)
  }
  buf = writeString(buf, 0, rows - 2, '='.repeat(cols), 4, 0)

  // Grid cells (checkerboard pattern)
  for (let y = 3; y < rows - 4; y++) {
    for (let x = 3; x < cols - 3; x++) {
      if ((x + y) % 4 === 0) {
        buf = writeString(buf, x, y, '.', 2, 0)
      } else if ((x + y) % 7 === 0) {
        buf = writeString(buf, x, y, '*', 5, 0)
      }
    }
  }

  // Status bar
  buf = writeString(buf, 1, rows - 3, ' Grid: 60x20  |  Mode: Edit  |  Zoom: 1.0x', 7, 0)

  gridEl.setBuffer(buf)
}

function loadMapDemo() {
  if (!gridEl) return
  let buf = createBuffer(cols, rows)

  buf = writeString(buf, 1, 0, 'uCode GridCore -- Map View', 7, 2, true)

  // Ocean
  buf = fill(buf, 0, 1, cols, rows - 2, '~', 4, 0)

  // Land masses
  buf = fill(buf, 5, 4, 12, 6, '#', 2, 0)
  buf = fill(buf, 30, 6, 8, 4, '#', 2, 0)
  buf = fill(buf, 45, 3, 10, 8, '#', 2, 0)

  // Cities
  buf = writeString(buf, 8, 6, '*', 1, 0)
  buf = writeString(buf, 9, 6, 'London', 7, 0)
  buf = writeString(buf, 33, 8, '*', 1, 0)
  buf = writeString(buf, 34, 8, 'Paris', 7, 0)
  buf = writeString(buf, 48, 5, '*', 1, 0)
  buf = writeString(buf, 49, 5, 'Berlin', 7, 0)

  // Coordinates
  buf = writeString(buf, 1, rows - 3, ' Lat: 51.5N  Lon: 0.1W  |  uCode: 0000001+ ', 7, 0)

  gridEl.setBuffer(buf)
}

function clearGrid() {
  gridEl?.clear()
}
</script>

<style scoped>
.ucode-viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: var(--usx-spacing-lg);
}

.ucode-info {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  font-family: monospace;
}
</style>
