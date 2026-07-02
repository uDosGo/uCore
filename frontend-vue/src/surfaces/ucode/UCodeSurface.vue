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
        <span class="ucode-actions-spacer"></span>
        <button class="surface-tab-nav__action-btn" title="Reload" @click="reloadGrid">
          <UIcon name="refresh" />
        </button>
        <button class="surface-tab-nav__action-btn" title="Save" @click="exportGrid">
          <UIcon name="save" />
        </button>
        <button class="surface-tab-nav__action-btn" title="Load" @click="triggerImport">
          <UIcon name="folder_open" />
        </button>
        <button
          class="surface-tab-nav__action-btn preset-toggle"
          title="Viewport presets"
          @click="showPresets = !showPresets"
        >
          <UIcon name="dashboard" />
        </button>
      </template>
    </SurfaceTabNav>

    <!-- ─── Layer Composer tab: prose stub ─── -->
    <div v-if="activeTab === 'layer'" class="surface__body">
      <div class="surface__canvas">
        <div class="layer-composer-prose">
          <h2>Layer Composer</h2>
          <p>Layer composer is the spatial and geographical linking of Layers into <strong>Worlds</strong>.</p>
          <p>This feature is under development. The linking system will connect map layers — terrain, structures, units — into unified spatial environments with geographical coordinates, adjacency rules, and world-level queries.</p>
          <ul>
            <li><a href="https://github.com/uDosGo/uCore/tree/main/docs" target="_blank" rel="noopener">uCore docs</a></li>
            <li><a href="https://github.com/uDosGo/uCore/tree/main/docs/specs" target="_blank" rel="noopener">Spatial / location specs</a></li>
            <li><a href="https://github.com/uDosGo/uCore/tree/main/docs/archived" target="_blank" rel="noopener">Geography / map layer archives</a></li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ─── Other non-grid tabs (Terminal / Teletext) ─── -->
    <template v-else-if="activeTab !== 'grid'">
    <div class="surface__body">
      <!-- Slide-in preset popover (floats over canvas) -->
      <div class="preset-popover" :class="{ open: showPresets }">
        <div class="preset-popover__inner">
          <button
            v-for="(p, i) in VIEWPORT_PRESETS" :key="p.name"
            class="preset-popover__item"
            :class="{ active: viewportIndex === i }"
            @click="selectPreset(i)"
          >
            <span class="preset-popover__dims">{{ p.cols }}×{{ p.rows }}</span>
            <span class="preset-popover__desc">{{ p.description }}</span>
          </button>
        </div>
      </div>
      <div class="surface__canvas">
        <div ref="gridContainer" class="ucode-viewport" role="region" :aria-label="`${currentTitle} viewport`"></div>
      </div>
    </div>
    </template>

    <!-- ─── Grid Editor tab: split layout ─── -->
    <div v-else class="grid-editor-layout">
      <!-- Slide-in preset popover (floats over editor) -->
      <div class="preset-popover" :class="{ open: showPresets }">
        <div class="preset-popover__inner">
          <button
            v-for="(p, i) in VIEWPORT_PRESETS" :key="p.name"
            class="preset-popover__item"
            :class="{ active: viewportIndex === i }"
            @click="selectPreset(i)"
          >
            <span class="preset-popover__dims">{{ p.cols }}×{{ p.rows }}</span>
            <span class="preset-popover__desc">{{ p.description }}</span>
          </button>
        </div>
      </div>
      <!-- Left: editor + layer overview -->
      <div class="grid-editor-main">
        <!-- ─── Editor section: 24×24 grid (left) + palette/tools (right) ─── -->
        <div class="editor-section">
          <div class="editor-section__viewport" ref="editorViewportRef">
            <span class="editor-section__label editor-section__label--overlay">Editor · {{ editorCols }}×{{ editorRows }}</span>
          </div>
          <div class="editor-section__side">
            <span class="editor-section__label">Tools</span>
            <div class="editor-section__tools">
              <button
                v-for="t in TOOLS" :key="t.id"
                class="editor-tool-btn"
                :class="{ active: currentTool === t.id }"
                :title="t.label"
                @click="currentTool = t.id"
              ><UIcon :name="t.icon" /></button>
            </div>

            <span class="editor-section__label">Palette</span>
            <div class="editor-section__colours">
              <button
                v-for="(c, i) in PALETTE" :key="i"
                class="editor-colour-swatch"
                :class="{ 'fg-active': selectedFg === i, 'bg-active': selectedBg === i }"
                :style="{ background: c.hex }"
                :title="c.name"
                @click="selectedFg = i"
                @click.right.prevent="selectedBg = i"
              >
                <span v-if="selectedFg === i" class="colour-marker fg">F</span>
                <span v-if="selectedBg === i" class="colour-marker bg">B</span>
              </button>
            </div>

            <span class="editor-section__label">Actions</span>
            <div class="editor-section__actions">
              <button class="editor-action-btn" @click="fillLayer" title="Fill all cells">Fill</button>
              <button class="editor-action-btn" @click="clearLayer" title="Clear layer">Clr</button>
              <button class="editor-action-btn" @click="exportGrid" title="Export as JSON">Exp</button>
              <button class="editor-action-btn" @click="triggerImport" title="Import JSON">Imp</button>
            </div>
            <input
              ref="importInputRef"
              type="file"
              accept=".json"
              style="display:none"
              @change="onImportFile"
            />
          </div>
        </div>

        <!-- ─── Layer section: 40×25 map (collapsible) ─── -->
        <div class="layer-section" :class="{ 'layer-section--collapsed': !layerExpanded }">
          <div class="layer-section__bar" @click="layerExpanded = !layerExpanded">
            <UIcon :name="layerExpanded ? 'expand_less' : 'expand_more'" class="layer-section__toggle" />
            <span class="editor-section__label">Layer · {{ layerCols }}×{{ layerRows }}</span>
            <span class="editor-section__label" style="opacity:0.5">
              Focus: ({{ editorFocusX }}, {{ editorFocusY }})
            </span>
          </div>
          <div class="layer-section__viewport" ref="layerViewportRef"></div>
        </div>
      </div>

      <!-- ─── Right sidebar: full height ─── -->
      <aside class="editor-sidebar">
        <!-- Font mapping -->
        <div class="sidebar-section">
          <h4 class="sidebar-title">Font</h4>
          <div class="sidebar-font-btns">
            <button
              class="sidebar-font-btn"
              :class="{ active: editorFont === 'pressstart2p' }"
              @click="editorFont = 'pressstart2p'"
            >Terminal</button>
            <button
              class="sidebar-font-btn"
              :class="{ active: editorFont === 'mode7gx3' }"
              @click="editorFont = 'mode7gx3'"
            >Teletext</button>
          </div>
        </div>

        <!-- Font character set -->
        <div class="sidebar-section sidebar-font-chars">
          <h4 class="sidebar-title">Characters</h4>
          <div class="sidebar-chars-grid">
            <button
              v-for="ch in fontChars" :key="ch"
              class="sidebar-char-chip"
              :class="{ selected: selectedChar === ch }"
              :style="{ fontFamily: chipFont }"
              :title="`U+${ch.charCodeAt(0).toString(16).toUpperCase().padStart(4,'0')}`"
              @click="placeChar(ch)"
            >{{ ch }}</button>
          </div>
        </div>

        <!-- Character input -->
        <div class="sidebar-section">
          <h4 class="sidebar-title">Active Char</h4>
          <div class="sidebar-char-row">
            <input
              class="sidebar-char-input"
              v-model="selectedChar"
              maxlength="1"
              placeholder="Char"
            />
            <span class="sidebar-char-code">{{ selectedCharCode }}</span>
          </div>
        </div>

      </aside>
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
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useShellStore } from '../../stores/shell'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'
import type { TabDef } from '../../skills/molecules/SurfaceTabNav.vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import { createGridUICanvas, type GridUICanvasElement } from '../../grid-core/gridui-canvas'
import { createBuffer, writeString, fill, scroll as scrollBuffer, cloneBuffer, clear as clearBuffer } from '../../grid-core/index'
import { PALETTE_DARK } from '../../grid-core/palette'
import { GRID_PRESETS } from '../../grid-core/algebra'
import type { GridBuffer, GridCell } from '../../grid-core/types'

const shell = useShellStore()

/* ─── Tab Definitions ─────────────────────────────────────────────── */
const UCODE_TABS: TabDef[] = [
  { id: 'terminal', label: 'Terminal', icon: 'terminal' },
  { id: 'teletext', label: 'Teletext', icon: 'tv' },
  { id: 'grid', label: 'Grid Editor', icon: 'grid_on' },
  { id: 'layer', label: 'Layer Composer', icon: 'layers' },
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
const tabConfigs: Record<string, { cols: number; rows: number; font: string; cellSize: number; charWidth?: number }> = {
  terminal: { cols: 40, rows: 25, font: 'pressstart2p', cellSize: 20 },
  teletext: { cols: 40, rows: 25, font: 'mode7gx3', cellSize: 20, charWidth: 26 },
  grid: { cols: 40, rows: 25, font: 'mode7gx3', cellSize: 20, charWidth: 26 },
  layer: { cols: 40, rows: 25, font: 'mode7gx3', cellSize: 20, charWidth: 26 },
}

const gridCols = computed(() => tabConfigs[activeTab.value]?.cols ?? 60)
const gridRows = computed(() => tabConfigs[activeTab.value]?.rows ?? 20)

/* ─── Single-Canvas Tabs ──────────────────────────────────────────── */
const gridContainer = ref<HTMLDivElement>()
const canvasCache = new Map<string, GridUICanvasElement>()
let activeCanvas: GridUICanvasElement | null = null
let terminalCursorY = 0

/* ─── Grid Editor State ───────────────────────────────────────────── */
const PALETTE = PALETTE_DARK

const TOOLS = [
  { id: 'pencil', label: 'Pencil', icon: 'edit' },
  { id: 'fill', label: 'Flood fill', icon: 'format_paint' },
  { id: 'erase', label: 'Eraser', icon: 'ink_eraser' },
  { id: 'eyedropper', label: 'Eyedropper', icon: 'colorize' },
] as const

const editorViewportRef = ref<HTMLDivElement>()
const layerViewportRef = ref<HTMLDivElement>()
const importInputRef = ref<HTMLInputElement>()

const showSidebar = ref(true)
const layerExpanded = ref(true)
const currentTool = ref<'pencil' | 'fill' | 'erase' | 'eyedropper'>('pencil')
const selectedFg = ref(7)
const selectedBg = ref(0)
const selectedChar = ref('#')
const editorFont = ref<'pressstart2p' | 'mode7gx3'>('mode7gx3')

/** Characters shown in the sidebar font char set */
const fontChars = computed(() => {
  if (editorFont.value === 'mode7gx3') {
    // Teletext G0 character set: printable ASCII + block graphics
    const chars: string[] = []
    for (let i = 0x20; i <= 0x7E; i++) chars.push(String.fromCharCode(i))
    // Add common teletext block chars
    chars.push('█', '▄', '▀', '▐', '▌', '░', '▒', '▓', '│', '─', '║', '═')
    chars.push('╔', '╗', '╚', '╝', '╠', '╣', '╦', '╩', '╬')
    return chars
  }
  // Press Start 2P: restricted to printable ASCII
  const chars: string[] = []
  for (let i = 0x21; i <= 0x7E; i++) chars.push(String.fromCharCode(i))
  return chars
})

function placeChar(ch: string) {
  selectedChar.value = ch
  // Write char to center cell of the editor viewport
  if (activeTab.value === 'grid') {
    const cx = editorFocusX.value + Math.floor(editorCols / 2)
    const cy = editorFocusY.value + Math.floor(editorRows / 2)
    if (cx >= 0 && cx < LAYER_COLS && cy >= 0 && cy < LAYER_ROWS) {
      layerBuffer[cy][cx] = { char: ch, fg: selectedFg.value, bg: selectedBg.value }
      syncEditorToFocus()
      renderLayerOverview()
    }
  }
}

const chipFont = computed(() =>
  editorFont.value === 'mode7gx3'
    ? "'MODE7GX3', monospace"
    : '"Press Start 2P", monospace'
)

const selectedCharCode = computed(() =>
  selectedChar.value
    ? `U+${selectedChar.value.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')}`
    : ''
)

/** Update canvas fonts when font selector changes */
watch(editorFont, (font) => {
  if (editorCanvas) editorCanvas.setAttribute('font', font)
  if (layerCanvas) layerCanvas.setAttribute('font', font)
})

// Layer grid dimensions (the full editable canvas)
// Default: 40×25 Teletext standard with 24×24 base cell
let LAYER_COLS = 40
let LAYER_ROWS = 25

// Viewport presets — cycled by toggle icon button
const VIEWPORT_PRESETS = GRID_PRESETS.filter(p =>
  ['editor','teletext','terminal','terminal-retro','teletext-retro',
   'square-60','square-80','classic-40x30','classic-80x60',
   'widescreen-80x45','widescreen-128x72','ultrawide-160x91'].includes(p.name)
)
const viewportIndex = ref(0)
const currentPreset = computed(() => VIEWPORT_PRESETS[viewportIndex.value])
const showPresets = ref(false)

function selectPreset(i: number) {
  viewportIndex.value = i
  showPresets.value = false
}

watch(viewportIndex, () => onPresetChange(currentPreset.value.name))

// Editor viewport dimensions (the visible 24x24 window into the layer)
const editorCols = 24
const editorRows = 24

// Reactive layer dimensions for template binding
const layerCols = ref(LAYER_COLS)
const layerRows = ref(LAYER_ROWS)

// Current focus — top-left corner of the editor viewport within the layer
const editorFocusX = ref(0)
const editorFocusY = ref(0)

// The full layer buffer
let layerBuffer: GridBuffer = createBuffer(LAYER_COLS, LAYER_ROWS)

// Canvas elements for the editor
let editorCanvas: GridUICanvasElement | null = null
let layerCanvas: GridUICanvasElement | null = null

/* ─── Lifecycle ───────────────────────────────────────────────────── */
onMounted(() => {
  if (!gridContainer.value) return
  if (activeTab.value !== 'grid') {
    initGrid(activeTab.value)
  } else {
    initGridEditor()
  }
})

onUnmounted(() => {
  canvasCache.forEach(el => el.remove())
  canvasCache.clear()
  activeCanvas = null
  editorCanvas?.remove()
  layerCanvas?.remove()
  editorCanvas = null
  layerCanvas = null
})

/* ─── Single-Canvas Tab Management ────────────────────────────────── */
function initGrid(tabId: string) {
  if (!gridContainer.value) return
  const cfg = tabConfigs[tabId]

  if (activeCanvas) activeCanvas.style.display = 'none'

  let el = canvasCache.get(tabId)
  if (!el) {
    el = createGridUICanvas({ cols: cfg.cols, rows: cfg.rows, font: cfg.font, cellSize: cfg.cellSize })
    if (cfg.charWidth) el.setAttribute('char-width', String(cfg.charWidth))
    el.style.flexShrink = '0'
    gridContainer.value.appendChild(el)
    canvasCache.set(tabId, el)
    activeCanvas = el
    loadTabContent(tabId)
  } else {
    // Update font and char-width when reusing cached canvas
    el.setAttribute('font', cfg.font)
    if (cfg.charWidth) el.setAttribute('char-width', String(cfg.charWidth))
    else el.removeAttribute('char-width')
    el.style.display = ''
    // Force reflow so parent clientHeight is valid for _fitToContainer
    void el.offsetHeight
    // Re-attach if detached (v-if destroys parent between tab switches)
    if (!gridContainer.value.contains(el)) {
      gridContainer.value.appendChild(el)
    }
    activeCanvas = el
    loadTabContent(tabId)
  }
}

watch(activeTab, (newTab) => {
  terminalCursorY = 0
  // Clean up grid editor canvases when leaving grid tab
  if (newTab !== 'grid') {
    editorCanvas?.remove()
    layerCanvas?.remove()
    editorCanvas = null
    layerCanvas = null
  }
  nextTick(() => {
    if (newTab === 'grid') {
      initGridEditor()
    } else if (gridContainer.value) {
      initGrid(newTab)
    }
  })
})

function loadTabContent(tabId?: string) {
  const id = tabId || activeTab.value
  switch (id) {
    case 'terminal': loadTerminalWelcome(); break
    case 'teletext': loadTeletextDemo(); break
    case 'layer': loadLayerDemo(); break
  }
}

/* ─── Grid Editor — Init ──────────────────────────────────────────── */
function createEditorBuffer(): GridBuffer {
  const buf = createBuffer(editorCols, editorRows)
  // Fill with some starter pattern
  for (let r = 0; r < editorRows; r++) {
    for (let c = 0; c < editorCols; c++) {
      if (c === 0 || c === editorCols - 1 || r === 0 || r === editorRows - 1) {
        buf[r][c] = { char: '.', fg: 4, bg: 0 }
      }
    }
  }
  return buf
}

function initGridEditor() {
  destroyGridEditor()
  if (!editorViewportRef.value || !layerViewportRef.value) return

  // Editor view: 24×24 cells, auto-fits container with gridlines
  editorCanvas = createGridUICanvas({ cols: editorCols, rows: editorRows, font: editorFont.value, cellSize: 100 })
  editorCanvas.setAttribute('gridlines', '')
  editorCanvas.style.flexShrink = '0'
  editorCanvas.addEventListener('cell-click', onEditorCellClick as EventListener)
  editorViewportRef.value.appendChild(editorCanvas)

  // Layer overview: 40×25 cells, auto-fits container
  layerCanvas = createGridUICanvas({ cols: LAYER_COLS, rows: LAYER_ROWS, font: editorFont.value, cellSize: 100 })
  layerCanvas.style.flexShrink = '0'
  layerCanvas.addEventListener('cell-click', onLayerCellClick as EventListener)
  layerViewportRef.value.appendChild(layerCanvas)

  // Fill layer with demo map content
  loadGridEditorDemo()
  renderLayerOverview()
  syncEditorToFocus()
}

function loadGridEditorDemo() {
  layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS)
  // Title
  layerBuffer = writeString(layerBuffer, 1, 0, 'uCode Grid Editor', 7, 5, true)
  // Fill with '.' background
  layerBuffer = fill(layerBuffer, 0, 1, LAYER_COLS, LAYER_ROWS - 2, '.', 4, 0)
  // Map layers
  const layers = [
    { label: 'Terrain', color: 2, y: 3, fillChar: '#' },
    { label: 'Structures', color: 3, y: 8, fillChar: '&' },
    { label: 'Units', color: 1, y: 13, fillChar: '@' },
  ]
  for (const layer of layers) {
    layerBuffer = fill(layerBuffer, 4, layer.y, 30, 3, layer.fillChar, layer.color, 0)
    layerBuffer = writeString(layerBuffer, 4, layer.y + 1, `  ~ ${layer.label} ~  `, 7, layer.color, true)
  }
  // Legend panel
  layerBuffer = writeString(layerBuffer, 40, 3, '╔══════════════╗', 6, 0)
  layerBuffer = writeString(layerBuffer, 40, 4, '║  Layer Stack ║', 6, 0)
  layerBuffer = writeString(layerBuffer, 40, 5, '╠══════════════╣', 6, 0)
  layerBuffer = writeString(layerBuffer, 40, 6, '║  1. Terrain  ║', 2, 0)
  layerBuffer = writeString(layerBuffer, 40, 7, '║  2. Structs  ║', 3, 0)
  layerBuffer = writeString(layerBuffer, 40, 8, '║  3. Units    ║', 1, 0)
  layerBuffer = writeString(layerBuffer, 40, 9, '╚══════════════╝', 6, 0)
  layerBuffer = writeString(layerBuffer, 1, LAYER_ROWS - 3, ' Click a cell to edit in the editor above', 7, 0)
}

function destroyGridEditor() {
  editorCanvas?.remove()
  layerCanvas?.remove()
  editorCanvas = null
  layerCanvas = null
}

/* ─── Grid Editor — Layer Overview ────────────────────────────────── */
function renderLayerOverview() {
  if (!layerCanvas) return
  layerCanvas.setBuffer(cloneBuffer(layerBuffer))
}

/* ─── Grid Editor — Sync Editor to Focus ──────────────────────────── */
function syncEditorToFocus() {
  if (!editorCanvas) return
  const fx = editorFocusX.value
  const fy = editorFocusY.value
  const buf = createBuffer(editorCols, editorRows)

  // Copy the visible region from layer into editor
  for (let r = 0; r < editorRows; r++) {
    for (let c = 0; c < editorCols; c++) {
      const lr = fy + r
      const lc = fx + c
      if (lr >= 0 && lr < LAYER_ROWS && lc >= 0 && lc < LAYER_COLS) {
        buf[r][c] = { ...layerBuffer[lr][lc] }
      }
    }
  }
  editorCanvas.setBuffer(buf)
}

/* ─── Grid Editor — Cell Click Handlers ───────────────────────────── */
function onLayerCellClick(e: CustomEvent) {
  const { col, row } = e.detail
  // Copy clicked cell's char/fg/bg to active editor state
  const cell = layerBuffer[row]?.[col]
  if (cell) {
    selectedChar.value = cell.char
    selectedFg.value = cell.fg
    selectedBg.value = cell.bg
  }
  // Center the editor viewport on the clicked chunk
  const chunkX = Math.floor(col / editorCols) * editorCols
  const chunkY = Math.floor(row / editorRows) * editorRows
  editorFocusX.value = Math.max(0, Math.min(chunkX, LAYER_COLS - editorCols))
  editorFocusY.value = Math.max(0, Math.min(chunkY, LAYER_ROWS - editorRows))
  syncEditorToFocus()
  renderLayerOverview()
}

function onEditorCellClick(e: CustomEvent) {
  const { col, row } = e.detail
  const fx = editorFocusX.value
  const fy = editorFocusY.value
  const lx = fx + col
  const ly = fy + row
  if (lx < 0 || lx >= LAYER_COLS || ly < 0 || ly >= LAYER_ROWS) return

  const tool = currentTool.value

  if (tool === 'eyedropper') {
    const cell = layerBuffer[ly][lx]
    selectedFg.value = cell.fg
    selectedBg.value = cell.bg
    selectedChar.value = cell.char
    currentTool.value = 'pencil'
    return
  }

  if (tool === 'erase') {
    layerBuffer[ly][lx] = { char: ' ', fg: 7, bg: 0 }
    syncEditorToFocus()
    renderLayerOverview()
    return
  }

  if (tool === 'fill') {
    floodFill(lx, ly, selectedFg.value, selectedBg.value, selectedChar.value)
    syncEditorToFocus()
    renderLayerOverview()
    return
  }

  // Pencil: draw the selected character with selected colours
  layerBuffer[ly][lx] = { char: selectedChar.value, fg: selectedFg.value, bg: selectedBg.value }
  syncEditorToFocus()
  renderLayerOverview()
}

/* ─── Grid Editor — Flood Fill ────────────────────────────────────── */
function floodFill(startX: number, startY: number, fg: number, bg: number, char: string) {
  const targetChar = layerBuffer[startY][startX].char
  const targetFg = layerBuffer[startY][startX].fg
  if (targetChar === char && targetFg === fg) return

  const stack: [number, number][] = [[startX, startY]]
  const visited = new Set<number>()

  while (stack.length > 0) {
    const [cx, cy] = stack.pop()!
    const key = cy * LAYER_COLS + cx
    if (visited.has(key)) continue
    visited.add(key)
    if (cx < 0 || cx >= LAYER_COLS || cy < 0 || cy >= LAYER_ROWS) continue

    const cell = layerBuffer[cy][cx]
    if (cell.char !== targetChar || cell.fg !== targetFg) continue

    layerBuffer[cy][cx] = { char, fg, bg }

    stack.push([cx - 1, cy], [cx + 1, cy], [cx, cy - 1], [cx, cy + 1])
  }
}

/* ─── Grid Editor — Actions ───────────────────────────────────────── */
function clearLayer() {
  layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS)
  editorFocusX.value = 0
  editorFocusY.value = 0
  syncEditorToFocus()
  renderLayerOverview()
}

function reloadGrid() {
  if (activeTab.value === 'grid' || activeTab.value === 'layer') {
    layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS)
    editorFocusX.value = 0
    editorFocusY.value = 0
    syncEditorToFocus()
    renderLayerOverview()
  } else {
    loadTabContent()
  }
}

function cycleViewport() {
  viewportIndex.value = (viewportIndex.value + 1) % VIEWPORT_PRESETS.length
}

function onPresetChange(name: string) {
  const p = GRID_PRESETS.find(x => x.name === name)
  if (!p) return
  LAYER_COLS = p.cols
  LAYER_ROWS = p.rows
  layerCols.value = p.cols
  layerRows.value = p.rows

  if (activeTab.value === 'grid' || activeTab.value === 'layer') {
    layerBuffer = createBuffer(p.cols, p.rows)
    editorFocusX.value = 0
    editorFocusY.value = 0
    destroyGridEditor()
    nextTick(() => initGridEditor())
  } else {
    // Rebuild single canvas at new size
    const cfg = tabConfigs[activeTab.value]
    if (cfg) {
      cfg.cols = p.cols
      cfg.rows = p.rows
    }
    const tab = activeTab.value
    // Destroy and recreate the canvas for this tab
    const old = canvasCache.get(tab)
    if (old) { old.remove(); canvasCache.delete(tab) }
    nextTick(() => initGrid(tab))
  }
}

function fillLayer() {
  for (let r = 0; r < LAYER_ROWS; r++) {
    for (let c = 0; c < LAYER_COLS; c++) {
      layerBuffer[r][c] = { char: selectedChar.value, fg: selectedFg.value, bg: selectedBg.value }
    }
  }
  syncEditorToFocus()
  renderLayerOverview()
}

function getExportBuffer(): GridBuffer {
  if (activeTab.value === 'grid' || activeTab.value === 'layer') return layerBuffer
  if (activeCanvas) return activeCanvas.buffer
  return createBuffer(40, 25)
}

function exportGrid() {
  const buf = getExportBuffer()
  const cols = buf.length > 0 ? buf[0].length : 40
  const rows = buf.length
  const data = {
    format: 'ucode-grid-v1',
    cols,
    rows,
    cells: buf.map(row => row.map(c => ({ c: c.char, f: c.fg, b: c.bg }))),
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ucode-grid-${cols}x${rows}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function triggerImport() {
  importInputRef.value?.click()
}

function onImportFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result as string)
      if (data.format !== 'ucode-grid-v1' || !data.cells) return

      const isGridLayer = activeTab.value === 'grid' || activeTab.value === 'layer'
      const target = isGridLayer ? layerBuffer : (activeCanvas?.buffer || null)
      if (!target) return

      const cols = Math.min(data.cols, target[0]?.length || 40)
      const rows = Math.min(data.rows, target.length)
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const src = data.cells[r]?.[c]
          if (src) target[r][c] = { char: src.c || ' ', fg: src.f ?? 7, bg: src.b ?? 0 }
        }
      }
      if (isGridLayer) {
        layerBuffer = cloneBuffer(layerBuffer)
        syncEditorToFocus()
        renderLayerOverview()
      } else if (activeCanvas) {
        activeCanvas.setBuffer(cloneBuffer(target))
      }
    } catch (err) {
      console.error('Import failed:', err)
    }
  }
  reader.readAsText(file)
  ;(e.target as HTMLInputElement).value = ''
}

/* ─── Teletext Tab ────────────────────────────────────────────────── */
function loadTeletextDemo() {
  if (!activeCanvas) return
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
  activeCanvas.setBuffer(buf)
}

/* ─── Terminal Tab ────────────────────────────────────────────────── */
function terminalPrintLine(text: string, fg = 7, bg = 0) {
  if (!activeCanvas) return
  const cfg = tabConfigs.terminal
  let buf = activeCanvas.buffer
  if (!buf || buf.length === 0) buf = createBuffer(cfg.cols, cfg.rows)
  if (terminalCursorY >= cfg.rows) {
    buf = scrollBuffer(buf, 1)
    terminalCursorY = cfg.rows - 1
  }
  buf = writeString(buf, 0, terminalCursorY, text, fg, bg)
  terminalCursorY++
  activeCanvas.setBuffer(buf)
}

function loadTerminalWelcome() {
  if (!activeCanvas) return
  terminalCursorY = 0
  let buf = createBuffer(tabConfigs.terminal.cols, tabConfigs.terminal.rows)
  activeCanvas.setBuffer(buf)
  terminalPrintLine('uDosConnect BBC BASIC Terminal', 4, 0)
  terminalPrintLine('='.repeat(tabConfigs.terminal.cols), 3, 0)
  terminalPrintLine('GridUI Canvas Engine  ·  40x25 Teletext', 2, 0)
  terminalPrintLine('Type HELP · DEMO · CLEAR · CLS · ABOUT', 7, 0)
  terminalPrintLine('', 7, 0)
  terminalCursorY = 6
}

/* ─── Layer Tab ────────────────────────────────────────────────────── */
function loadLayerDemo() {
  if (!activeCanvas) return
  const cfg = tabConfigs.layer
  let buf = createBuffer(cfg.cols, cfg.rows)
  buf = writeString(buf, 1, 0, 'uCode GridCore -- Layer View', 7, 5, true)
  buf = fill(buf, 0, 1, cfg.cols, cfg.rows - 2, '.', 4, 0)
  const layers = [
    { label: 'Terrain', color: 2, y: 3, fillChar: '#' },
    { label: 'Structures', color: 3, y: 8, fillChar: '&' },
    { label: 'Units', color: 1, y: 13, fillChar: '@' },
  ]
  for (const layer of layers) {
    buf = fill(buf, 4, layer.y, 30, 3, layer.fillChar, layer.color, 0)
    buf = writeString(buf, 4, layer.y + 1, `  ~ ${layer.label} ~  `, 7, layer.color, true)
  }
  buf = writeString(buf, 40, 3, '╔══════════════╗', 6, 0)
  buf = writeString(buf, 40, 4, '║  Layer Stack ║', 6, 0)
  buf = writeString(buf, 40, 5, '╠══════════════╣', 6, 0)
  buf = writeString(buf, 40, 6, '║  1. Terrain  ║', 2, 0)
  buf = writeString(buf, 40, 7, '║  2. Structs  ║', 3, 0)
  buf = writeString(buf, 40, 8, '║  3. Units    ║', 1, 0)
  buf = writeString(buf, 40, 9, '╚══════════════╝', 6, 0)
  buf = writeString(buf, 1, cfg.rows - 3, ' Layers: 3  |  Active: Terrain  |  Opacity: 100%', 7, 0)
  buf = writeString(buf, 25, 0, 'Click a cell to edit', 6, 0)
  activeCanvas.setBuffer(buf)
}

/* ─── Common ──────────────────────────────────────────────────────── */
function clearGrid() {
  activeCanvas?.clear()
}
</script>

<style scoped>
/* ─── Single-canvas viewport (non-grid tabs) ────────────────────── */
.ucode-viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 5%;
}

.ucode-viewport gridui-canvas {
  flex-shrink: 0;
}

/* ─── Grid Editor Layout ────────────────────────────────────────── */
.grid-editor-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  gap: 0;
}

.grid-editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  gap: 0;
}

/* ─── Editor section: grid left, tools+palette right ────────────── */
.editor-section {
  flex: 1;
  display: flex;
  flex-direction: row;
  min-height: 0;
  overflow: hidden;
  gap: var(--usx-spacing-sm);
}

.editor-section__viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
  background: var(--usx-color-background-alt, #111);
  border-radius: var(--usx-radius-md, 6px);
}

.editor-section__label {
  font-size: var(--usx-font-size-sm);
  font-weight: 600;
  color: var(--usx-color-on-surface);
  font-family: monospace;
}

.editor-section__label--overlay {
  position: absolute;
  top: var(--usx-spacing-xs);
  left: var(--usx-spacing-sm);
  opacity: 0.5;
  pointer-events: none;
}

/* Side panel: tools and palette stacked */
.editor-section__side {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 2px;
  width: 180px;
}

.editor-section__tools {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  justify-content: center;
}

.editor-tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  min-height: 0;
  border: 1px solid var(--usx-color-border);
  border-radius: 4px;
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  font-size: 16px;
  cursor: pointer;
  padding: 0;
  box-sizing: border-box;
}

.editor-tool-btn:hover {
  background: var(--usx-color-surface-hover);
  border-color: var(--usx-color-primary);
}

.editor-tool-btn.active {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-color: var(--usx-color-primary);
}

.editor-section__colours {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  justify-content: center;
}

.editor-colour-swatch {
  width: 20px;
  height: 20px;
  min-height: 0;
  border: 2px solid var(--usx-color-border);
  border-radius: 3px;
  cursor: pointer;
  padding: 0;
  box-sizing: border-box;
  transition: transform 0.1s ease, border-color 0.1s ease;
}

.editor-colour-swatch:hover {
  transform: scale(1.15);
  z-index: 1;
}

.editor-colour-swatch.fg-active {
  border-color: var(--usx-color-primary);
  box-shadow: 0 0 0 2px var(--usx-color-primary);
}

.editor-colour-swatch.bg-active {
  border-color: var(--usx-color-warning);
  box-shadow: 0 0 0 2px var(--usx-color-warning);
}

.editor-section__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  justify-content: center;
}

.editor-action-btn {
  font-size: 9px;
  font-family: monospace;
  font-weight: 600;
  padding: 3px 4px;
  min-height: 0;
  height: auto;
  border: 1px solid var(--usx-color-border);
  border-radius: 3px;
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
}

.editor-action-btn:hover {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
}

.editor-action-btn:hover {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  background: var(--usx-color-surface-hover);
}

/* ─── Layer section (bottom half, collapsible) ──────────────────── */
.layer-section {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  min-height: 80px;
  max-height: 45%;
  overflow: hidden;
  transition: max-height 0.25s ease, min-height 0.25s ease;
}

.layer-section--collapsed {
  max-height: 32px;
  min-height: 32px;
}

.layer-section--collapsed .layer-section__viewport {
  display: none;
}

.layer-section__bar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  flex-shrink: 0;
  cursor: pointer;
  user-select: none;
}

.layer-section__bar:hover {
  background: var(--usx-color-surface-hover, rgba(128,128,128,0.05));
}

.layer-section__toggle {
  font-size: 18px;
  color: var(--usx-color-on-surface-muted);
}

.layer-section__viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  background: var(--usx-color-background-alt, #111);
  border-radius: var(--usx-radius-md, 6px);
  padding: var(--usx-spacing-xs);
}

/* ─── Sidebar ───────────────────────────────────────────────────── */
.editor-sidebar {
  width: var(--usx-sidebar-width, 280px);
  flex-shrink: 0;
  overflow-y: auto;
  border-left: 1px solid var(--usx-color-border);
  background: var(--usx-color-surface);
  padding: var(--usx-sidebar-padding, var(--usx-spacing-md));
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.sidebar-title {
  font-size: 10px;
  font-weight: 600;
  margin: 0;
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Font mapping */
.sidebar-font-btns {
  display: flex;
  gap: 2px;
}

.sidebar-font-btn {
  flex: 1;
  padding: 3px var(--usx-spacing-xs);
  border: 1px solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  cursor: pointer;
  border-radius: 3px;
  font-size: 11px;
  font-family: monospace;
  transition: background var(--usx-transition-fast), border-color var(--usx-transition-fast);
}

.sidebar-font-btn:hover {
  background: var(--usx-color-surface-hover);
  border-color: var(--usx-color-primary);
}

.sidebar-font-btn.active {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-color: var(--usx-color-primary);
}

/* Font character grid */
.sidebar-font-chars {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.sidebar-chars-grid {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 1px;
}

.sidebar-char-chip {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  aspect-ratio: 1;
  border: 1px solid var(--usx-color-border);
  border-radius: 2px;
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  cursor: pointer;
  font-family: monospace;
  font-size: var(--usx-font-size-base, 14px);
  transition: background var(--usx-transition-fast), border-color var(--usx-transition-fast);
}

.sidebar-char-chip:hover {
  background: var(--usx-color-surface-hover);
  border-color: var(--usx-color-primary);
}

.sidebar-char-chip.selected {
  border-color: var(--usx-color-primary);
  background: var(--usx-color-primary-container, rgba(0,120,255,0.15));
}

/* Character input */
.sidebar-char-row {
  display: flex;
  gap: var(--usx-spacing-xs);
  align-items: center;
}

.sidebar-char-input {
  width: 48px;
  text-align: center;
  font-size: 20px;
  font-family: monospace;
  padding: var(--usx-spacing-xs);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm, 4px);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
}

.sidebar-char-code {
  font-size: 10px;
  font-family: monospace;
  color: var(--usx-color-on-surface-muted);
}

/* Tool/action buttons */
.sidebar-tool-row {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.sidebar-action-btn {
  flex: 1;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  cursor: pointer;
  border-radius: var(--usx-radius-sm, 4px);
  font-size: var(--usx-font-size-sm);
  font-family: monospace;
  transition: background var(--usx-transition-fast), border-color var(--usx-transition-fast);
}

.sidebar-action-btn:hover {
  background: var(--usx-color-surface-hover);
  border-color: var(--usx-color-primary);
}

/* Colour markers (F/B labels on swatches) */
.colour-marker {
  position: absolute;
  font-size: 9px;
  font-weight: 700;
  font-family: monospace;
  line-height: 1;
  padding: 1px 2px;
  border-radius: 2px;
  pointer-events: none;
}

.colour-marker.fg {
  top: 1px;
  left: 1px;
  background: rgba(0,0,0,0.6);
  color: #fff;
}

.colour-marker.bg {
  bottom: 1px;
  right: 1px;
  background: rgba(255,255,255,0.8);
  color: #000;
}

/* Layer Composer prose stub */
.layer-composer-prose {
  max-width: var(--usx-prose-width, 72ch);
  margin: var(--usx-spacing-xl) auto;
  padding: var(--usx-spacing-xl);
}

.layer-composer-prose h2 {
  font-size: var(--usx-font-size-2xl, 24px);
  margin: 0 0 var(--usx-spacing-md);
  color: var(--usx-color-on-surface);
}

.layer-composer-prose p {
  margin: 0 0 var(--usx-spacing-md);
  color: var(--usx-color-on-surface);
  line-height: 1.6;
}

.layer-composer-prose ul {
  margin: 0;
  padding-left: var(--usx-spacing-lg);
}

.layer-composer-prose a {
  color: var(--usx-color-primary);
  text-decoration: underline;
}

/* ─── Shared ────────────────────────────────────────────────────── */
.ucode-info {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  font-family: monospace;
  margin-left: var(--usx-spacing-xs);
  white-space: nowrap;
}

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

/* ─── Viewport preset floating popover ────────────────────────── */
.ucode-actions-spacer {
  flex: 1;
}

.surface__body,
.surface__canvas,
.grid-editor-layout {
  position: relative;
}

.preset-popover {
  position: absolute;
  top: 0;
  right: 0;
  left: auto;
  z-index: 10;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.25s ease;
}

.preset-popover.open {
  max-height: 500px;
}

.preset-popover__inner {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--usx-spacing-xs);
  background: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: 0 0 var(--usx-radius-sm, 4px) var(--usx-radius-sm, 4px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 260px;
}

.preset-popover__item {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--usx-spacing-xs);
  width: 100%;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: 1px solid transparent;
  border-radius: var(--usx-radius-sm, 4px);
  background: transparent;
  color: var(--usx-color-on-surface);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  font-family: monospace;
  white-space: nowrap;
  text-align: right;
  transition: background var(--usx-transition-fast), border-color var(--usx-transition-fast);
}

.preset-popover__item:hover {
  background: var(--usx-color-surface-hover, rgba(128,128,128,0.1));
  border-color: var(--usx-color-primary);
}

.preset-popover__item.active {
  border-color: var(--usx-color-primary);
  background: var(--usx-color-primary-container, rgba(0,120,255,0.1));
}

.preset-popover__dims {
  font-weight: var(--usx-font-weight-semibold, 600);
}

.preset-popover__desc {
  color: var(--usx-color-on-surface-muted);
}
</style>
