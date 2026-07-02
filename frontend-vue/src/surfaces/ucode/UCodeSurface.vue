<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <!-- Tab navigation: Terminal | Teletext | Grid | Layer -->
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="UCODE_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    >
      <template #actions>
        <button
          v-if="activeTab === 'grid'"
          class="surface-tab-nav__action-btn"
          title="Grid demo"
          @click="loadGridDemo"
        >
          <UIcon name="grid_on" />
        </button>
        <button
          v-if="activeTab === 'grid'"
          class="surface-tab-nav__action-btn"
          title="Map view"
          @click="loadMapDemo"
        >
          <UIcon name="map" />
        </button>
        <button
          v-if="activeTab === 'layer'"
          class="surface-tab-nav__action-btn"
          title="Layer demo"
          @click="loadLayerDemo"
        >
          <UIcon name="layers" />
        </button>
        <button
          v-if="activeTab === 'teletext'"
          class="surface-tab-nav__action-btn"
          title="Teletext demo"
          @click="loadTeletextDemo"
        >
          <UIcon name="tv" />
        </button>
        <button
          v-if="activeTab === 'terminal'"
          class="surface-tab-nav__action-btn"
          title="Terminal demo"
          @click="loadTerminalWelcome"
        >
          <UIcon name="play_arrow" />
        </button>
        <button
          class="surface-tab-nav__action-btn"
          title="Clear"
          @click="clearGrid"
        >
          <UIcon name="delete_sweep" />
        </button>
        <span class="ucode-info">{{ gridCols }}×{{ gridRows }}</span>
      </template>
    </SurfaceTabNav>
    <div class="surface__body">
      <!-- Grid Viewport -->
      <div class="surface__canvas">
        <div ref="gridContainer" class="ucode-viewport" role="region" :aria-label="`${currentTitle} viewport`"></div>
      </div>


    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component UCodeSurface
 * @description uCode/GridCore surface — unified hub for Grid editor, Teletext viewer, and Terminal emulator.
 * All three modes use the framework-agnostic <gridui-canvas> Web Component (gridcore embeddable).
 * @category surfaces
 * @usage Routed at '/ucode'.
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useShellStore } from '../../stores/shell'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'
import type { TabDef } from '../../skills/molecules/SurfaceTabNav.vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import { createGridUICanvas, type GridUICanvasElement } from '../../grid-core/gridui-canvas'
import { createBuffer, writeString, fill, scroll as scrollBuffer } from '../../grid-core/index'

const shell = useShellStore()

/* ─── Tab Definitions ─────────────────────────────────────────────── */
const UCODE_TABS: TabDef[] = [
  { id: 'terminal', label: 'Terminal', icon: 'terminal' },
  { id: 'teletext', label: 'Teletext', icon: 'tv' },
  { id: 'grid', label: 'Grid', icon: 'grid_on' },
  { id: 'layer', label: 'Layer', icon: 'layers' },
]

const activeTab = ref('terminal')

const tabTitles: Record<string, string> = {
  terminal: 'uCode — Terminal',
  teletext: 'uCode — Teletext',
  grid: 'uCode — Grid Editor',
  layer: 'uCode — Layer',
}

const currentTitle = computed(() => tabTitles[activeTab.value] || 'uCode — GridCore')

/* ─── Grid Configs ────────────────────────────────────────────────── */
const tabConfigs: Record<string, { cols: number; rows: number; font: string; cellSize: number }> = {
  terminal: { cols: 80, rows: 24, font: 'pressstart2p', cellSize: 16 },
  teletext: { cols: 40, rows: 25, font: 'vt323', cellSize: 20 },
  grid: { cols: 60, rows: 20, font: 'pressstart2p', cellSize: 16 },
  layer: { cols: 60, rows: 20, font: 'pressstart2p', cellSize: 16 },
}

const gridCols = computed(() => tabConfigs[activeTab.value]?.cols ?? 60)
const gridRows = computed(() => tabConfigs[activeTab.value]?.rows ?? 20)

/* ─── Refs ────────────────────────────────────────────────────────── */
const gridContainer = ref<HTMLDivElement>()
let gridEl: GridUICanvasElement | null = null
let terminalCursorY = 0

/* ─── Lifecycle ───────────────────────────────────────────────────── */
onMounted(() => {
  if (!gridContainer.value) return
  initGrid()
})

onUnmounted(() => {
  destroyGrid()
})

/* ─── Grid Management ─────────────────────────────────────────────── */
function initGrid() {
  destroyGrid()
  if (!gridContainer.value) return
  const cfg = tabConfigs[activeTab.value]
  gridEl = createGridUICanvas({
    cols: cfg.cols,
    rows: cfg.rows,
    font: cfg.font,
    cellSize: cfg.cellSize,
  })
  gridContainer.value.appendChild(gridEl)
  loadTabContent()
}

function destroyGrid() {
  gridEl?.remove()
  gridEl = null
}

function recreateGrid() {
  if (!gridContainer.value) return
  initGrid()
}

/* ─── Tab switching ──────────────────────────────────────────────── */
watch(activeTab, () => {
  terminalCursorY = 0
  recreateGrid()
})

function loadTabContent() {
  switch (activeTab.value) {
    case 'terminal':
      loadTerminalWelcome()
      break
    case 'teletext':
      loadTeletextDemo()
      break
    case 'grid':
      loadGridDemo()
      break
    case 'layer':
      loadLayerDemo()
      break
  }
}

/* ─── Grid Tab ────────────────────────────────────────────────────── */
function loadGridDemo() {
  if (!gridEl) return
  const cfg = tabConfigs.grid
  let buf = createBuffer(cfg.cols, cfg.rows)

  buf = writeString(buf, 1, 0, 'uCode GridCore -- Grid Editor', 7, 4, true)
  buf = writeString(buf, 0, 1, '='.repeat(cfg.cols), 4, 0)
  for (let y = 2; y < cfg.rows - 2; y++) {
    buf = writeString(buf, 0, y, '|', 4, 0)
    buf = writeString(buf, cfg.cols - 1, y, '|', 4, 0)
  }
  buf = writeString(buf, 0, cfg.rows - 2, '='.repeat(cfg.cols), 4, 0)

  for (let y = 3; y < cfg.rows - 4; y++) {
    for (let x = 3; x < cfg.cols - 3; x++) {
      if ((x + y) % 4 === 0) {
        buf = writeString(buf, x, y, '.', 2, 0)
      } else if ((x + y) % 7 === 0) {
        buf = writeString(buf, x, y, '*', 5, 0)
      }
    }
  }

  buf = writeString(buf, 1, cfg.rows - 3, ' Grid: 60x20  |  Mode: Edit  |  Zoom: 1.0x', 7, 0)
  gridEl.setBuffer(buf)
}

function loadMapDemo() {
  if (!gridEl) return
  const cfg = tabConfigs.grid
  let buf = createBuffer(cfg.cols, cfg.rows)

  buf = writeString(buf, 1, 0, 'uCode GridCore -- Map View', 7, 2, true)
  buf = fill(buf, 0, 1, cfg.cols, cfg.rows - 2, '~', 4, 0)
  buf = fill(buf, 5, 4, 12, 6, '#', 2, 0)
  buf = fill(buf, 30, 6, 8, 4, '#', 2, 0)
  buf = fill(buf, 45, 3, 10, 8, '#', 2, 0)
  buf = writeString(buf, 8, 6, '*', 1, 0)
  buf = writeString(buf, 9, 6, 'London', 7, 0)
  buf = writeString(buf, 33, 8, '*', 1, 0)
  buf = writeString(buf, 34, 8, 'Paris', 7, 0)
  buf = writeString(buf, 48, 5, '*', 1, 0)
  buf = writeString(buf, 49, 5, 'Berlin', 7, 0)
  buf = writeString(buf, 1, cfg.rows - 3, ' Lat: 51.5N  Lon: 0.1W  |  uCode: 0000001+ ', 7, 0)
  gridEl.setBuffer(buf)
}

/* ─── Teletext Tab ────────────────────────────────────────────────── */
function loadTeletextDemo() {
  if (!gridEl) return
  const cfg = tabConfigs.teletext
  let buf = createBuffer(cfg.cols, cfg.rows)

  buf = writeString(buf, 1, 0, 'uDosConnect Teletext', 7, 4, true)
  buf = writeString(buf, 30, 0, 'P100', 7, 4)
  buf = writeString(buf, 0, 1, '='.repeat(cfg.cols), 3, 0)
  buf = writeString(buf, 2, 3, 'Welcome to uCore Teletext', 7, 0, true)
  buf = writeString(buf, 2, 5, 'GridUI Canvas Engine -- Live', 2, 0)
  buf = writeString(buf, 2, 7, 'Framework-agnostic Web Component', 6, 0)
  buf = writeString(buf, 2, 9, 'Powered by grid-algebra + bbcruntime', 5, 0)
  buf = writeString(buf, 2, 12, 'X'.repeat(36), 4, 0)
  buf = writeString(buf, 2, 13, 'X  Teletext G0 Character Set    X', 4, 0)
  buf = writeString(buf, 2, 14, 'X  Block graphics + mosaic       X', 4, 0)
  buf = writeString(buf, 2, 15, 'X'.repeat(36), 4, 0)
  buf = writeString(buf, 0, cfg.rows - 2, '='.repeat(cfg.cols), 3, 0)
  buf = writeString(buf, 1, cfg.rows - 1, 'uDosConnect', 7, 1)
  buf = writeString(buf, 28, cfg.rows - 1, 'Page 100', 7, 1)

  gridEl.setBuffer(buf)
}

/* ─── Terminal Tab ────────────────────────────────────────────────── */
function terminalPrintLine(text: string, fg = 7, bg = 0) {
  if (!gridEl) return
  const cfg = tabConfigs.terminal
  let buf = gridEl.buffer
  // Ensure buffer is initialized (gridEl starts with empty buffer)
  if (!buf || buf.length === 0) {
    buf = createBuffer(cfg.cols, cfg.rows)
  }
  if (terminalCursorY >= cfg.rows) {
    buf = scrollBuffer(buf, 1)
    terminalCursorY = cfg.rows - 1
  }
  buf = writeString(buf, 0, terminalCursorY, text, fg, bg)
  terminalCursorY++
  gridEl.setBuffer(buf)
}

function loadTerminalWelcome() {
  if (!gridEl) return
  terminalCursorY = 0
  let buf = createBuffer(tabConfigs.terminal.cols, tabConfigs.terminal.rows)
  gridEl.setBuffer(buf)
  terminalPrintLine('uDosConnect BBC BASIC Terminal', 4, 0)
  terminalPrintLine('='.repeat(tabConfigs.terminal.cols), 3, 0)
  terminalPrintLine('GridUI Canvas Engine -- Framework-Agnostic Web Component', 2, 0)
  terminalPrintLine('Type "HELP" for commands, "DEMO" for a demo.', 7, 0)
  terminalPrintLine('', 7, 0)
  terminalCursorY = 6
}

/* ─── Layer Tab ────────────────────────────────────────────────────── */
function loadLayerDemo() {
  if (!gridEl) return
  const cfg = tabConfigs.layer
  let buf = createBuffer(cfg.cols, cfg.rows)

  buf = writeString(buf, 1, 0, 'uCode GridCore -- Layer View', 7, 5, true)
  buf = fill(buf, 0, 1, cfg.cols, cfg.rows - 2, '.', 4, 0)

  // Render a few sample layers
  const layers = [
    { label: 'Terrain', color: 2, y: 3, fillChar: '#' },
    { label: 'Structures', color: 3, y: 8, fillChar: '&' },
    { label: 'Units', color: 1, y: 13, fillChar: '@' },
  ]
  for (const layer of layers) {
    buf = fill(buf, 4, layer.y, 30, 3, layer.fillChar, layer.color, 0)
    buf = writeString(buf, 4, layer.y + 1, `  ~ ${layer.label} ~  `, 7, layer.color, true)
  }

  // Layer legend
  buf = writeString(buf, 40, 3, '╔══════════════╗', 6, 0)
  buf = writeString(buf, 40, 4, '║  Layer Stack ║', 6, 0)
  buf = writeString(buf, 40, 5, '╠══════════════╣', 6, 0)
  buf = writeString(buf, 40, 6, '║  1. Terrain  ║', 2, 0)
  buf = writeString(buf, 40, 7, '║  2. Structs  ║', 3, 0)
  buf = writeString(buf, 40, 8, '║  3. Units    ║', 1, 0)
  buf = writeString(buf, 40, 9, '╚══════════════╝', 6, 0)

  buf = writeString(buf, 1, cfg.rows - 3, ' Layers: 3  |  Active: Terrain  |  Opacity: 100%', 7, 0)
  gridEl.setBuffer(buf)
}

/* ─── Common ──────────────────────────────────────────────────────── */
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
  overflow: hidden;
  padding: 5%;
}

.ucode-viewport gridui-canvas {
  width: 100%;
  height: 100%;
}

.ucode-info {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  font-family: monospace;
  margin-left: var(--usx-spacing-xs);
  white-space: nowrap;
}

/* ─── Tab nav action buttons (icon-only toolbar) ────────────────── */
.surface-tab-nav__action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min, 32px);
  height: var(--usx-touch-min, 32px);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  border-radius: var(--usx-border-radius-sm, 4px);
  transition: color var(--usx-transition-fast), background var(--usx-transition-fast);
  -webkit-appearance: none;
  appearance: none;
  flex-shrink: 0;
}

.surface-tab-nav__action-btn:hover {
  color: var(--usx-color-primary);
  background: var(--usx-color-surface-hover, rgba(128, 128, 128, 0.1));
}

.surface-tab-nav__action-btn:active {
  color: var(--usx-color-primary-active, var(--usx-color-primary));
}


</style>
