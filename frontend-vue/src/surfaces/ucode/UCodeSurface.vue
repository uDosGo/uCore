<template>
  <div
    class="surface gridcore-surface"
    :class="[
      gridcorePresetClass,
      { 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' },
    ]"
  >
    <!-- Tab navigation: Terminal | Teletext | Pixel | Grid | Layer -->
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

    <!-- ─── Pixel Editor tab: per-pixel character designer ─── -->
    <div v-else-if="activeTab === 'pixel'" class="pixel-editor-layout">
      <div class="pixel-editor-body">
        <div class="pixel-editor-main">
          <!-- Toolbar: dimensions, tools, actions, palette — inside same content div -->
          <div class="pixel-toolbar">
            <div class="pixel-toolbar__dims">
              <input class="pixel-toolbar__input" type="number" v-model.number="pixelW" min="4" max="128" @change="onPixelResize" />
              <span class="pixel-toolbar__sep">×</span>
              <input class="pixel-toolbar__input" type="number" v-model.number="pixelH" min="4" max="128" @change="onPixelResize" />
            </div>
            <div class="pixel-toolbar__tools">
              <button v-for="t in PIXEL_TOOLS" :key="t.id" class="pixel-tool-btn" :class="{ active: pixelTool === t.id }" :title="t.label" @click="pixelTool = t.id"><UIcon :name="t.icon" /></button>
            </div>
            <div class="pixel-toolbar__actions">
              <button class="pixel-toolbar__action-btn" title="Clear all pixels" @click="clearPixelEditor">Clear</button>
              <button class="pixel-toolbar__action-btn" title="Invert pixels" @click="invertPixelEditor">Invert</button>
              <button class="pixel-toolbar__action-btn" title="Export pixel data" @click="exportPixelData">Export</button>
            </div>
            <div class="pixel-toolbar__palette">
              <button class="pixel-tool-btn" :class="{ active: showColorPopover }" title="Colour Picker" @click="showColorPopover = !showColorPopover" @blur="hideColorPopover">
                <UIcon name="palette" />
              </button>
              <!-- 3×3 colour grid popover -->
              <div class="pixel-colour-popover" v-if="showColorPopover" @mousedown.prevent>
                <button
                  v-for="(c, i) in PALETTE" :key="i"
                  class="pixel-colour-popover__swatch"
                  :class="[`pixel-colour-popover__swatch--${i}`, { 'fg-active': pixelFg === i, 'bg-active': pixelBg === i }]"
                  :title="c.name + (pixelFg === i ? ' FG' : pixelBg === i ? ' BG' : '') + ' | L-click FG · R-click BG'"
                  @click="pixelFg = i"
                  @click.right.prevent="pixelBg = i"
                >
                  <span v-if="pixelFg === i" class="colour-marker fg">F</span>
                  <span v-if="pixelBg === i" class="colour-marker bg">B</span>
                </button>
                <!-- 9th cell: transparent/empty -->
                <button
                  class="pixel-colour-popover__swatch pixel-colour-popover__swatch--empty"
                  :class="{ 'bg-active': pixelBg === -1 }"
                  title="Transparent / Empty | L-click FG · R-click BG"
                  @click="pixelFg = -1"
                  @click.right.prevent="pixelBg = -1"
                >
                  <span v-if="pixelBg === -1" class="colour-marker bg">B</span>
                </button>
              </div>
            </div>
          </div>
          <div class="pixel-canvas-wrapper" ref="pixelCanvasRef" tabindex="0" @keydown="onPixelKeydown">
            <span class="editor-section__label editor-section__label--overlay">
              Pixel Editor · {{ pixelW }}×{{ pixelH }} · {{ selectedChar || '?' }} · {{ pixelFont === 'mode7gx3' ? 'Teletext' : 'Terminal' }}
            </span>
          </div>
        </div>
        <!-- Sidebar: font, character library, active glyph -->
        <aside class="editor-sidebar">
          <div class="sidebar-section">
            <h4 class="sidebar-title">Font</h4>
            <div class="sidebar-font-btns">
              <button class="sidebar-font-btn" :class="{ active: pixelFont === 'pressstart2p' }" @click="pixelFont = 'pressstart2p'">Terminal</button>
              <button class="sidebar-font-btn" :class="{ active: pixelFont === 'mode7gx3' }" @click="pixelFont = 'mode7gx3'">Teletext</button>
            </div>
          </div>
          <div class="sidebar-section">
            <h4 class="sidebar-title">Active Glyph</h4>
            <div class="sidebar-char-row">
              <input class="sidebar-char-input" v-model="selectedChar" maxlength="1" placeholder="Char" />
              <span class="sidebar-char-code">{{ selectedCharCode }}</span>
            </div>
          </div>
          <div class="sidebar-section sidebar-font-chars">
            <h4 class="sidebar-title">Character Library</h4>
            <div class="sidebar-chars-grid">
              <button
                v-for="ch in pixelChars" :key="ch"
                class="sidebar-char-chip"
                :class="{ selected: selectedChar === ch }"
                :title="`U+${ch.charCodeAt(0).toString(16).toUpperCase().padStart(4,'0')}`"
                @click="selectPixelChar(ch)"
              >{{ ch }}</button>
            </div>
          </div>
        </aside>
      </div>
    </div>

    <!-- ─── Grid Builder tab: Layer Editor ─── -->
    <div v-else-if="activeTab === 'grid'" class="grid-editor-layout">
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
      <div class="grid-editor-main">
        <!-- Layer Editor — full layer as primary editing surface -->
        <div class="layer-editor-primary">
          <div class="layer-editor__toolbar">
            <div class="layer-editor__dims">
              <input class="layer-editor__input" type="number" v-model.number="layerCols" min="4" max="256" @change="onLayerResize" />
              <span class="layer-editor__sep">×</span>
              <input class="layer-editor__input" type="number" v-model.number="layerRows" min="4" max="256" @change="onLayerResize" />
            </div>
            <div class="layer-editor__tools">
              <button v-for="t in TOOLS" :key="t.id" class="pixel-tool-btn" :class="{ active: currentTool === t.id }" :title="t.label" @click="currentTool = t.id"><UIcon :name="t.icon" /></button>
            </div>
            <div class="layer-editor__actions">
              <button class="pixel-toolbar__action-btn" @click="fillLayer" title="Fill all cells">Fill</button>
              <button class="pixel-toolbar__action-btn" @click="clearLayer" title="Clear layer">Clr</button>
              <button class="pixel-toolbar__action-btn" @click="exportGrid" title="Export as JSON">Exp</button>
              <button class="pixel-toolbar__action-btn" @click="triggerImport" title="Import JSON">Imp</button>
            </div>
            <div class="layer-editor__palette">
              <button class="pixel-tool-btn" :class="{ active: showLayerColorPopover }" title="Colour Picker" @click="showLayerColorPopover = !showLayerColorPopover" @blur="hideLayerColorPopover">
                <UIcon name="palette" />
              </button>
              <!-- 3×3 colour grid popover -->
              <div class="layer-colour-popover" v-if="showLayerColorPopover" @mousedown.prevent>
                <button
                  v-for="(c, i) in PALETTE" :key="i"
                  class="layer-colour-popover__swatch"
                  :class="[`layer-colour-popover__swatch--${i}`, { 'fg-active': selectedFg === i, 'bg-active': selectedBg === i }]"
                  :title="c.name + (selectedFg === i ? ' FG' : selectedBg === i ? ' BG' : '') + ' | L-click FG · R-click BG'"
                  @click="selectedFg = i"
                  @click.right.prevent="selectedBg = i"
                >
                  <span v-if="selectedBg === i" class="colour-marker bg">B</span>
                </button>
                <!-- 9th cell: transparent/empty -->
                <button
                  class="layer-colour-popover__swatch layer-colour-popover__swatch--empty"
                  :class="{ 'bg-active': selectedBg === -1 }"
                  title="Transparent / Empty | R-click BG"
                  @click="selectedFg = -1"
                  @click.right.prevent="selectedBg = -1"
                >
                  <span v-if="selectedBg === -1" class="colour-marker bg">B</span>
                </button>
              </div>
            </div>
            <span class="layer-editor__info">{{ currentTool }} · ({{ layerCursorCol }}, {{ layerCursorRow }})</span>
          </div>
          <div class="layer-editor__viewport" ref="layerViewportRef" tabindex="0" @keydown="onLayerKeydown" @mousedown="onLayerMouseDown"></div>
          <input ref="importInputRef" type="file" accept=".json" class="ucode-import-input" @change="onImportFile" />
        </div>
      </div>
      <!-- Sidebar: brush palette for placing chars into grid -->
      <aside class="editor-sidebar">
        <div class="sidebar-section">
          <h4 class="sidebar-title">Brush</h4>
          <div class="sidebar-font-btns">
            <button class="sidebar-font-btn" :class="{ active: editorFont === 'pressstart2p' }" @click="editorFont = 'pressstart2p'">Terminal</button>
            <button class="sidebar-font-btn" :class="{ active: editorFont === 'mode7gx3' }" @click="editorFont = 'mode7gx3'">Teletext</button>
          </div>
        </div>
        <div class="sidebar-section sidebar-font-chars">
          <h4 class="sidebar-title">Characters</h4>
          <div class="sidebar-chars-grid">
            <button
              v-for="ch in fontChars" :key="ch"
              class="sidebar-char-chip"
              :class="{ selected: selectedChar === ch }"
              :title="`U+${ch.charCodeAt(0).toString(16).toUpperCase().padStart(4,'0')}`"
              @click="selectBrushChar(ch)"
            >{{ ch }}</button>
          </div>
        </div>
        <div class="sidebar-section">
          <h4 class="sidebar-title">Active Char</h4>
          <div class="sidebar-char-row">
            <input class="sidebar-char-input" v-model="selectedChar" maxlength="1" placeholder="Char" />
            <span class="sidebar-char-code">{{ selectedCharCode }}</span>
          </div>
        </div>
      </aside>
    </div>

    <!-- ─── Terminal / Teletext tabs ─── -->
    <template v-else>
    <div class="surface__body">
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
        <div
          ref="gridContainer"
          class="ucode-viewport"
          role="region"
          tabindex="0"
          :aria-label="`${currentTitle} viewport`"
          @keydown="onTerminalKeydown"
        ></div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * @component UCodeSurface
 * @description uCode/GridCore surface — unified hub with Pixel Editor, Grid Builder, and Layer Composer.
 * All modes use the framework-agnostic <gridui-canvas> Web Component.
 * @category surfaces
 * @usage Routed at '/ucode'.
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useShellStore } from '../../stores/shell'
import { useGridCoreSettingsStore } from '../../stores/gridcoreSettings'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'
import type { TabDef } from '../../skills/molecules/SurfaceTabNav.vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import { createGridUICanvas, type GridUICanvasElement } from '../../grid-core/gridui-canvas'
import { createBuffer, writeString, fill, scroll as scrollBuffer, cloneBuffer, clear as clearBuffer, scaleBuffer } from '../../grid-core/index'
import { PALETTE_DARK } from '../../grid-core/palette'
import { GRID_PRESETS } from '../../grid-core/algebra'
import { G0Renderer } from '../../grid-core/g0-renderer'
import type { GridBuffer, GridCell } from '../../grid-core/types'

const g0r = new G0Renderer()

const shell = useShellStore()
const gridcoreSettings = useGridCoreSettingsStore()
const gridcorePresetClass = computed(() => `gridcore-surface--${gridcoreSettings.preset}`)

/* ─── Tab Definitions ─────────────────────────────────────────────── */
const UCODE_TABS: TabDef[] = [
  { id: 'terminal', label: 'Terminal', icon: 'terminal' },
  { id: 'teletext', label: 'Teletext', icon: 'tv' },
  { id: 'pixel', label: 'Pixel', icon: 'grid_on' },
  { id: 'grid', label: 'Grid', icon: 'dashboard' },
  { id: 'layer', label: 'Layer', icon: 'layers' },
]

const activeTab = ref('terminal')

const tabTitles: Record<string, string> = {
  terminal: 'uCode — Terminal',
  teletext: 'uCode — Teletext',
  pixel: 'uCode — Pixel Editor',
  grid: 'uCode — Layer Editor',
  layer: 'uCode — Layer Composer',
}

const currentTitle = computed(() => tabTitles[activeTab.value] || 'uCode — GridCore')

/* ─── Grid Configs ────────────────────────────────────────────────── */
const tabConfigs: Record<string, { cols: number; rows: number; font: string; cellSize: number; charWidth?: number }> = {
  terminal: { cols: 40, rows: 25, font: 'pressstart2p', cellSize: 20 },
  teletext: { cols: 40, rows: 25, font: 'mode7gx3', cellSize: 20, charWidth: 26 },
  pixel: { cols: 24, rows: 24, font: 'mode7gx3', cellSize: 24, charWidth: 24 },
  grid: { cols: 40, rows: 25, font: 'mode7gx3', cellSize: 20, charWidth: 26 },
  layer: { cols: 40, rows: 25, font: 'mode7gx3', cellSize: 20, charWidth: 26 },
}

/* ─── Single-Canvas Tabs ──────────────────────────────────────────── */
const gridContainer = ref<HTMLDivElement>()
const canvasCache = new Map<string, GridUICanvasElement>()
let activeCanvas: GridUICanvasElement | null = null
let terminalSocket: WebSocket | null = null
let terminalCursorX = 0
let terminalCursorY = 0

const UCORE_API = import.meta.env.VITE_UCORE_URL || import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

/* ─── Shared Brush State (persists across Pixel/Grid tabs) ─────────── */
const PALETTE = PALETTE_DARK

const TOOLS = [
  { id: 'pencil', label: 'Pencil', icon: 'edit' },
  { id: 'fill', label: 'Flood fill', icon: 'format_paint' },
  { id: 'erase', label: 'Eraser', icon: 'ink_eraser' },
  { id: 'eyedropper', label: 'Eyedropper', icon: 'colorize' },
] as const

// Pixel Editor tools
const PIXEL_TOOLS = [
  { id: 'pencil', label: 'Pencil', icon: 'edit' },
  { id: 'erase', label: 'Eraser', icon: 'ink_eraser' },
  { id: 'fill', label: 'Flood fill', icon: 'format_paint' },
] as const

const pixelTool = ref<'pencil' | 'erase' | 'fill'>('pencil')
const showColorPopover = ref(false)
const showLayerColorPopover = ref(false)

function hideColorPopover() { setTimeout(() => { showColorPopover.value = false }, 200) }
function hideLayerColorPopover() { setTimeout(() => { showLayerColorPopover.value = false }, 200) }

// Pixel Editor dimensions (editable by user from toolbar)
const pixelW = ref(24)
const pixelH = ref(24)

// Pixel Editor colors (independent from Grid tab)
const pixelFg = ref(7)
const pixelBg = ref(0)

const selectedFg = ref(7)
const selectedBg = ref(0)
const selectedChar = ref('#')
const editorFont = ref<'pressstart2p' | 'mode7gx3'>('mode7gx3')
const currentTool = ref<'pencil' | 'fill' | 'erase' | 'eyedropper'>('pencil')

const selectedCharCode = computed(() =>
  selectedChar.value
    ? `U+${selectedChar.value.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')}`
    : ''
)

/** Characters shown in the Pixel sidebar character library — dynamic per font */
const pixelFont = ref<'pressstart2p' | 'mode7gx3'>('mode7gx3')

const pixelChars = computed(() => {
    if (pixelFont.value === 'pressstart2p') {
      const chars: string[] = []
      for (let i = 0x21; i <= 0x7E; i++) chars.push(String.fromCharCode(i))
      return chars
    }
    // mode7gx3: ASCII + G0 blocks
    const chars: string[] = []
    for (let i = 0x20; i <= 0x7E; i++) chars.push(String.fromCharCode(i))
    chars.push('█', '▄', '▀', '▐', '▌', '░', '▒', '▓', '│', '─', '║', '═')
    chars.push('╔', '╗', '╚', '╝', '╠', '╣', '╦', '╩', '╬')
    return chars
})

// Re-fill grid and update canvas font when font changes in Pixel tab
watch(pixelFont, (font) => {
  if (pixelCanvas) pixelCanvas.setAttribute('font', font)
  if (activeTab.value !== 'pixel') return
  fillPixelGridWithChar()
})

/** Characters shown in the Grid sidebar font char set */
const fontChars = computed(() => {
  if (editorFont.value === 'mode7gx3') {
    const chars: string[] = []
    for (let i = 0x20; i <= 0x7E; i++) chars.push(String.fromCharCode(i))
    chars.push('█', '▄', '▀', '▐', '▌', '░', '▒', '▓', '│', '─', '║', '═')
    chars.push('╔', '╗', '╚', '╝', '╠', '╣', '╦', '╩', '╬')
    return chars
  }
  const chars: string[] = []
  for (let i = 0x21; i <= 0x7E; i++) chars.push(String.fromCharCode(i))
  return chars
})

/** Set brush char (used by sidebar chips in both Pixel and Grid tabs) */
function selectBrushChar(ch: string) {
  selectedChar.value = ch
}

/** Pixel Editor: select character AND fill grid cells with it immediately */
function selectPixelChar(ch: string) {
  selectedChar.value = ch
  fillPixelGridWithChar()
}

/* ─── Grid Layer State ────────────────────────────────────────────── */
let LAYER_COLS = 40
let LAYER_ROWS = 25
const layerCols = ref(LAYER_COLS)
const layerRows = ref(LAYER_ROWS)

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

const layerCursorCol = ref(0)
const layerCursorRow = ref(0)
let layerBuffer: GridBuffer = createBuffer(LAYER_COLS, LAYER_ROWS)
let layerIsDragging = false

/* ─── Canvas refs & elements ──────────────────────────────────────── */
const layerViewportRef = ref<HTMLDivElement>()
const pixelCanvasRef = ref<HTMLDivElement>()
const importInputRef = ref<HTMLInputElement>()

let layerCanvas: GridUICanvasElement | null = null
let pixelCanvas: GridUICanvasElement | null = null

/* ─── Watchers ────────────────────────────────────────────────────── */
watch(editorFont, (font) => {
  if (layerCanvas) layerCanvas.setAttribute('font', font)
})

/* ─── Pixel Editor ─────────────────────────────────────────────────── */
let pixelBuffer: GridBuffer = createBuffer(24, 24)

/** Get the current "on" character — the actual glyph being edited */

/** Render the selected character's glyph as a bitmap across the pixel grid.
 *  Uses the G0 renderer to get a 12×10 binary bitmap, then nearest-neighbour
 *  scales it to fill pixelW × pixelH cells. "On" pixels show the actual character,
 *  "off" pixels show space + BG. */
function fillPixelGridWithChar() {
  const ch = selectedChar.value || ' '
  const w = pixelW.value
  const h = pixelH.value
  const charCode = ch.charCodeAt(0)
  const fg = pixelFg.value
  const bg = pixelBg.value

  const bitmap = g0r.getBitmap(charCode)
  const sw = Math.max(1, Math.round(w / 12))
  const sh = Math.max(1, Math.round(h / 10))

  for (let r = 0; r < h; r++) {
    const srcRow = Math.min(Math.floor(r / sh), 9)
    for (let c = 0; c < w; c++) {
      const srcCol = Math.min(Math.floor(c / sw), 11)
      const isFg = bitmap[srcRow * 12 + srcCol] === 1
      if (isFg) {
        pixelBuffer[r][c] = { char: ch, fg, bg: 0 }
      } else {
        pixelBuffer[r][c] = { char: ' ', fg: 0, bg }
      }
    }
  }
  pixelCanvas?.setBuffer(cloneBuffer(pixelBuffer))
}

function initPixelEditor() {
  if (!pixelCanvasRef.value) return
  pixelCanvas?.remove()
  const w = pixelW.value
  const h = pixelH.value
  pixelCanvas = createGridUICanvas({ cols: w, rows: h, font: pixelFont.value, cellSize: 24 })
  pixelCanvas.setAttribute('gridlines', '')
  pixelCanvas.style.flexShrink = '0'
  pixelCanvas.addEventListener('cell-click', onPixelClick as EventListener)
  pixelCanvasRef.value.appendChild(pixelCanvas)

  // Seed pixel buffer with selected character
  pixelBuffer = createBuffer(w, h)
  fillPixelGridWithChar()
}

// When selectedChar changes in Pixel tab, show it in the grid
watch(selectedChar, (ch) => {
  if (activeTab.value !== 'pixel') return
  fillPixelGridWithChar()
})

function onPixelResize() {
  // Clamp dimensions and re-initialise
  pixelW.value = Math.max(4, Math.min(128, pixelW.value))
  pixelH.value = Math.max(4, Math.min(128, pixelH.value))
  initPixelEditor()
}

/** Toggle a single pixel cell on/off. On = actual glyph char, Off = space+BG. */
function onPixelClick(e: CustomEvent) {
  const { col, row } = e.detail
  const w = pixelW.value
  const h = pixelH.value
  if (col < 0 || col >= w || row < 0 || row >= h) return
  const cell = pixelBuffer[row][col]
  const isOn = cell.char !== ' '
  const isTransparent = pixelFg.value === -1

  if (pixelTool.value === 'erase' || isTransparent || (pixelTool.value === 'pencil' && isOn)) {
    pixelBuffer[row][col] = { char: ' ', fg: 0, bg: pixelBg.value < 0 ? 0 : pixelBg.value }
  } else if (pixelTool.value === 'fill') {
    floodFillPixel(col, row)
  } else {
    pixelBuffer[row][col] = { char: selectedChar.value, fg: pixelFg.value, bg: 0 }
  }
  pixelCanvas?.setBuffer(cloneBuffer(pixelBuffer))
}

function floodFillPixel(startCol: number, startRow: number) {
  const w = pixelW.value
  const h = pixelH.value
  const target = pixelBuffer[startRow]?.[startCol]
  if (!target) return
  const targetIsOn = target.char !== ' '
  const newChar = pixelTool.value === 'erase' ? ' ' : selectedChar.value
  const newFg = pixelTool.value === 'erase' ? 0 : pixelFg.value
  if (target.char === newChar && target.fg === newFg) return

  const stack = [[startCol, startRow]]
  const visited = new Set<string>()
  while (stack.length > 0) {
    const [c, r] = stack.pop()!
    const key = `${c},${r}`
    if (visited.has(key)) continue
    if (c < 0 || c >= w || r < 0 || r >= h) continue
    const cell = pixelBuffer[r]?.[c]
    if (!cell) continue
    const cellIsOn = cell.char !== ' '
    if (cellIsOn !== targetIsOn) continue
    visited.add(key)
    if (cellIsOn) {
      pixelBuffer[r][c] = { char: newChar, fg: newFg, bg: 0 }
    } else {
      pixelBuffer[r][c] = { char: ' ', fg: 0, bg: pixelBg.value }
    }
    stack.push([c - 1, r], [c + 1, r], [c, r - 1], [c, r + 1])
  }
  pixelCanvas?.setBuffer(cloneBuffer(pixelBuffer))
}

function clearPixelEditor() {
  for (let r = 0; r < pixelH.value; r++) {
    for (let c = 0; c < pixelW.value; c++) {
      pixelBuffer[r][c] = { char: ' ', fg: 0, bg: 0 }
    }
  }
  pixelCanvas?.setBuffer(cloneBuffer(pixelBuffer))
}

function invertPixelEditor() {
  const ch = selectedChar.value
  for (let r = 0; r < pixelH.value; r++) {
    for (let c = 0; c < pixelW.value; c++) {
      const cell = pixelBuffer[r]?.[c]
      if (!cell) continue
      if (cell.char !== ' ') {
        cell.char = ' '
        cell.fg = 0
        cell.bg = pixelBg.value
      } else {
        cell.char = ch
        cell.fg = pixelFg.value
        cell.bg = 0
      }
    }
  }
  pixelCanvas?.setBuffer(cloneBuffer(pixelBuffer))
}

function exportPixelData() {
  const data = {
    format: 'ucore-pixel-v1',
    width: pixelW.value,
    height: pixelH.value,
    glyph: selectedChar.value || ' ',
    fg: pixelFg.value,
    bg: pixelBg.value,
    cells: pixelBuffer.map(row => row.map(cell => ({ c: cell.char, f: cell.fg, b: cell.bg }))),
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `pixel-${selectedChar.value || 'glyph'}-${pixelW.value}x${pixelH.value}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function onPixelKeydown(e: KeyboardEvent) {
  if (activeTab.value !== 'pixel') return
  if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
    e.preventDefault()
    selectedChar.value = e.key
  }
}

/* ─── Grid Tab (Layer Editor) ─────────────────────────────────────── */

function initGridEditor() {
  destroyGridEditor()
  if (!layerViewportRef.value) return

  layerCanvas = createGridUICanvas({ cols: LAYER_COLS, rows: LAYER_ROWS, font: editorFont.value, cellSize: 100 })
  layerCanvas.style.flexShrink = '0'
  layerCanvas.addEventListener('cell-click', onLayerCellClick as EventListener)
  layerViewportRef.value.appendChild(layerCanvas)

  loadGridEditorDemo()
  renderLayerBuffer()
}

function loadGridEditorDemo() {
  layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS)
  layerBuffer = writeString(layerBuffer, 1, 0, 'uCode Grid', 7, 5, true)
  layerBuffer = fill(layerBuffer, 0, 1, LAYER_COLS, LAYER_ROWS - 2, '.', 4, 0)
  const layers = [
    { label: 'Terrain', color: 2, y: 3, fillChar: '#' },
    { label: 'Structures', color: 3, y: 8, fillChar: '&' },
    { label: 'Units', color: 1, y: 13, fillChar: '@' },
  ]
  for (const lyr of layers) {
    layerBuffer = fill(layerBuffer, 4, lyr.y, 30, 3, lyr.fillChar, lyr.color, 0)
    layerBuffer = writeString(layerBuffer, 4, lyr.y + 1, `  ~ ${lyr.label} ~  `, 7, lyr.color, true)
  }
}

function destroyGridEditor() {
  layerCanvas?.remove()
  layerCanvas = null
}

function renderLayerBuffer() {
  if (!layerCanvas) return
  const buf = cloneBuffer(layerBuffer)
  // Highlight cursor cell
  const cr = layerCursorRow.value
  const cc = layerCursorCol.value
  if (cr >= 0 && cr < LAYER_ROWS && cc >= 0 && cc < LAYER_COLS) {
    const cell = buf[cr][cc]
    buf[cr][cc] = { ...cell, fg: cell.bg, bg: cell.fg === cell.bg ? (cell.fg === 0 ? 7 : 0) : cell.fg }
  }
  layerCanvas.setBuffer(buf)
}

/* ─── Grid Tab — Interaction ──────────────────────────────────────── */

function onLayerKeydown(e: KeyboardEvent) {
  if (activeTab.value !== 'grid') return
  switch (e.key) {
    case 'ArrowLeft': e.preventDefault(); layerCursorCol.value = Math.max(0, layerCursorCol.value - 1); renderLayerBuffer(); break
    case 'ArrowRight': e.preventDefault(); layerCursorCol.value = Math.min(LAYER_COLS - 1, layerCursorCol.value + 1); renderLayerBuffer(); break
    case 'ArrowUp': e.preventDefault(); layerCursorRow.value = Math.max(0, layerCursorRow.value - 1); renderLayerBuffer(); break
    case 'ArrowDown': e.preventDefault(); layerCursorRow.value = Math.min(LAYER_ROWS - 1, layerCursorRow.value + 1); renderLayerBuffer(); break
    case 'Tab':
      e.preventDefault()
      { const tools = TOOLS.map(t => t.id); const idx = tools.indexOf(currentTool.value); currentTool.value = tools[(idx + 1) % tools.length] as typeof currentTool.value }
      break
    default:
      if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault()
        const lx = layerCursorCol.value
        const ly = layerCursorRow.value
        if (lx >= 0 && lx < LAYER_COLS && ly >= 0 && ly < LAYER_ROWS) {
          layerBuffer[ly][lx] = { char: e.key, fg: selectedFg.value, bg: selectedBg.value }
          renderLayerBuffer()
        }
      }
      break
  }
}

function onLayerMouseDown(e: MouseEvent) {
  layerIsDragging = true
  const onMove = (ev: MouseEvent) => {
    if (!layerIsDragging || !layerCanvas) return
    const rect = layerCanvas.getBoundingClientRect()
    const localX = ev.clientX - rect.left
    const localY = ev.clientY - rect.top
    const cssW = parseFloat(layerCanvas.style.width || '0')
    const cssH = parseFloat(layerCanvas.style.height || '0')
    if (!cssW || !cssH) return
    const cellW = cssW / LAYER_COLS
    const cellH = cssH / LAYER_ROWS
    const col = Math.floor(localX / cellW)
    const row = Math.floor(localY / cellH)
    if (col >= 0 && col < LAYER_COLS && row >= 0 && row < LAYER_ROWS) {
      layerCursorCol.value = col
      layerCursorRow.value = row
      doLayerPaint()
    }
  }
  const onUp = () => {
    layerIsDragging = false
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

function doLayerPaint() {
  const lx = layerCursorCol.value
  const ly = layerCursorRow.value
  if (lx < 0 || lx >= LAYER_COLS || ly < 0 || ly >= LAYER_ROWS) return
  const tool = currentTool.value
  if (tool === 'eyedropper') {
    const cell = layerBuffer[ly][lx]
    selectedFg.value = cell.fg; selectedBg.value = cell.bg; selectedChar.value = cell.char
    currentTool.value = 'pencil'
    return
  }
  if (tool === 'erase') { layerBuffer[ly][lx] = { char: ' ', fg: 7, bg: 0 }; renderLayerBuffer(); return }
  layerBuffer[ly][lx] = { char: selectedChar.value, fg: selectedFg.value, bg: selectedBg.value }
  renderLayerBuffer()
}

function onLayerCellClick(e: CustomEvent) {
  const { col, row } = e.detail
  layerCursorCol.value = col
  layerCursorRow.value = row
  if (col < 0 || col >= LAYER_COLS || row < 0 || row >= LAYER_ROWS) return
  const tool = currentTool.value
  if (tool === 'eyedropper') {
    const cell = layerBuffer[row][col]
    selectedFg.value = cell.fg; selectedBg.value = cell.bg; selectedChar.value = cell.char
    currentTool.value = 'pencil'
    renderLayerBuffer()
    return
  }
  if (tool === 'erase') { layerBuffer[row][col] = { char: ' ', fg: 7, bg: 0 }; renderLayerBuffer(); return }
  if (tool === 'fill') { floodFill(col, row, selectedFg.value, selectedBg.value, selectedChar.value); renderLayerBuffer(); return }
  layerBuffer[row][col] = { char: selectedChar.value, fg: selectedFg.value, bg: selectedBg.value }
  renderLayerBuffer()
}

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

function clearLayer() { layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS); renderLayerBuffer() }
function fillLayer() {
  for (let r = 0; r < LAYER_ROWS; r++) for (let c = 0; c < LAYER_COLS; c++) layerBuffer[r][c] = { char: selectedChar.value, fg: selectedFg.value, bg: selectedBg.value }
  renderLayerBuffer()
}

function onPresetChange(name: string) {
  const p = GRID_PRESETS.find(x => x.name === name)
  if (!p) return
  const oldBuffer = cloneBuffer(layerBuffer)
  LAYER_COLS = p.cols; LAYER_ROWS = p.rows
  layerCols.value = p.cols; layerRows.value = p.rows
  if (activeTab.value === 'grid' || activeTab.value === 'layer') {
    layerBuffer = scaleBuffer(oldBuffer, p.cols, p.rows)
    layerCursorCol.value = 0; layerCursorRow.value = 0
    destroyGridEditor()
    nextTick(() => initGridEditor())
  } else {
    const cfg = tabConfigs[activeTab.value]
    if (cfg) { cfg.cols = p.cols; cfg.rows = p.rows }
    const tab = activeTab.value
    const old = canvasCache.get(tab)
    if (old) { old.remove(); canvasCache.delete(tab) }
    nextTick(() => initGrid(tab))
  }
}

/* ─── Layer resize ──────────────────────────────────────────────── */
function onLayerResize() {
  const newCols = Math.max(4, Math.min(256, layerCols.value))
  const newRows = Math.max(4, Math.min(256, layerRows.value))
  if (newCols === LAYER_COLS && newRows === LAYER_ROWS) return
  const oldBuffer = cloneBuffer(layerBuffer)
  LAYER_COLS = newCols; LAYER_ROWS = newRows
  layerCols.value = newCols; layerRows.value = newRows
  layerBuffer = scaleBuffer(oldBuffer, newCols, newRows)
  layerCursorCol.value = Math.min(layerCursorCol.value, newCols - 1)
  layerCursorRow.value = Math.min(layerCursorRow.value, newRows - 1)
  destroyGridEditor()
  nextTick(() => initGridEditor())
}

/* ─── Lifecycle ───────────────────────────────────────────────────── */
onMounted(() => {
  if (activeTab.value === 'pixel') initPixelEditor()
  else if (activeTab.value === 'grid') initGridEditor()
  else if (gridContainer.value) initGrid(activeTab.value)
})

onUnmounted(() => {
  disconnectTerminalRuntime()
  canvasCache.forEach(el => el.remove())
  canvasCache.clear()
  activeCanvas = null
  layerCanvas?.remove(); pixelCanvas?.remove()
  layerCanvas = null; pixelCanvas = null
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
    if (tabId === 'teletext') el.setAttribute('fit-container', 'false')
    el.style.flexShrink = '0'
    gridContainer.value.appendChild(el)
    canvasCache.set(tabId, el)
    activeCanvas = el
    loadTabContent(tabId)
  } else {
    el.setAttribute('font', cfg.font)
    if (cfg.charWidth) el.setAttribute('char-width', String(cfg.charWidth))
    else el.removeAttribute('char-width')
    if (tabId === 'teletext') el.setAttribute('fit-container', 'false')
    else el.removeAttribute('fit-container')
    el.style.display = ''
    void el.offsetHeight
    if (!gridContainer.value.contains(el)) gridContainer.value.appendChild(el)
    activeCanvas = el
    loadTabContent(tabId)
  }
}

watch(activeTab, (newTab) => {
  if (newTab !== 'terminal') disconnectTerminalRuntime()
  terminalCursorX = 0
  terminalCursorY = 0
  // Tear down previous grid editor
  layerCanvas?.remove()
  layerCanvas = null
  // Tear down pixel editor if leaving
  if (newTab !== 'pixel') { pixelCanvas?.remove(); pixelCanvas = null }
  nextTick(() => {
    if (newTab === 'pixel') initPixelEditor()
    else if (newTab === 'grid') initGridEditor()
    else if (gridContainer.value) initGrid(newTab)
  })
})

function loadTabContent(tabId?: string) {
  const id = tabId || activeTab.value
  switch (id) { case 'terminal': loadTerminalRuntime(); break; case 'teletext': loadTeletextDemo(); break; case 'layer': loadLayerDemo(); break }
}

function reloadGrid() {
  if (activeTab.value === 'pixel') { pixelBuffer = createBuffer(pixelW.value, pixelH.value); pixelCanvas?.setBuffer(cloneBuffer(pixelBuffer)) }
  else if (activeTab.value === 'grid' || activeTab.value === 'layer') { layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS); renderLayerBuffer() }
  else loadTabContent()
}

/* ─── Export/Import ────────────────────────────────────────────────── */
function getExportBuffer(): GridBuffer {
  if (activeTab.value === 'pixel') return pixelBuffer
  if (activeTab.value === 'grid' || activeTab.value === 'layer') return layerBuffer
  if (activeCanvas) return activeCanvas.buffer
  return createBuffer(40, 25)
}

function exportGrid() {
  const buf = getExportBuffer()
  const cols = buf.length > 0 ? buf[0].length : 40
  const rows = buf.length
  const data = { format: 'ucode-grid-v1', cols, rows, cells: buf.map(row => row.map(c => ({ c: c.char, f: c.fg, b: c.bg }))) }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `ucode-grid-${cols}x${rows}.json`; a.click()
  URL.revokeObjectURL(url)
}

function triggerImport() { importInputRef.value?.click() }

function onImportFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result as string)
      if (data.format !== 'ucode-grid-v1' || !data.cells) return
      const isPixel = activeTab.value === 'pixel'
      const isGridLayer = activeTab.value === 'grid' || activeTab.value === 'layer'
      const target = isPixel ? pixelBuffer : isGridLayer ? layerBuffer : (activeCanvas?.buffer || null)
      if (!target) return
      const cols = Math.min(data.cols, target[0]?.length || 40)
      const rows = Math.min(data.rows, target.length)
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const src = data.cells[r]?.[c]
          if (src) target[r][c] = { char: src.c || ' ', fg: src.f ?? 7, bg: src.b ?? 0 }
        }
      }
      if (isPixel) { pixelCanvas?.setBuffer(cloneBuffer(pixelBuffer)) }
      else if (isGridLayer) { layerBuffer = cloneBuffer(layerBuffer); renderLayerBuffer() }
      else if (activeCanvas) { activeCanvas.setBuffer(cloneBuffer(target)) }
    } catch (err) { console.error('Import failed:', err) }
  }
  reader.readAsText(file); (e.target as HTMLInputElement).value = ''
}

/* ─── Teletext Tab ────────────────────────────────────────────────── */
function loadTeletextDemo() {
  if (!activeCanvas) return
  const cfg = tabConfigs.teletext
  const c = cfg.cols, r = cfg.rows
  let buf = createBuffer(c, r)
  buf = fill(buf, 0, 0, c, 1, ' ', 7, 4)
  buf = writeString(buf, 1, 0, 'uCore TELETEXT  ·  GridUI Canvas Engine  ·  P100', 7, 4)
  buf = writeString(buf, c - 11, 0, 'Fri  3 Jul 2026', 7, 4)
  buf = fill(buf, 0, 1, c, 1, ' ', 7, 1)
  buf = writeString(buf, 1, 1, '═══  NEWS  ═══  WEATHER  ═══  SPORT  ═══  SCIENCE  ═══  GRID  ═══', 7, 1)
  buf = writeString(buf, 0, 2, '='.repeat(c), 3, 0)
  buf = writeString(buf, 2, 3, 'uCode GridUI v3 ships with Ceefax G0 emulation', 7, 0, true)
  buf = writeString(buf, 2, 4, 'MODE7GX3 bitmap renderer brings authentic teletext', 6, 0)
  buf = writeString(buf, 2, 5, 'pixel-crisp graphics to the 24x24 cell grid', 6, 0)
  buf = writeString(buf, 0, 7, '─'.repeat(19), 3, 0)
  buf = writeString(buf, 1, 8, 'G0 BITMAP ENGINE', 7, 0)
  buf[8][17] = { char: '│', fg: 3, bg: 0 }
  buf = writeString(buf, 1, 9, 'The new G0 renderer', 2, 0)
  buf = writeString(buf, 1, 10, 'renders MODE7GX3 chars', 2, 0)
  buf = writeString(buf, 1, 11, 'via offscreen canvas,', 2, 0)
  buf = writeString(buf, 1, 12, 'threshold to binary,', 2, 0)
  buf = writeString(buf, 1, 13, 'and NN scaling — zero', 2, 0)
  buf = writeString(buf, 20, 8, 'AUTO-FIT CONTAINERS', 7, 0)
  buf[8][37] = { char: '│', fg: 3, bg: 0 }
  buf = writeString(buf, 20, 9, 'Both the 24x24 editor', 5, 0)
  buf = writeString(buf, 20, 10, 'and 40x25 layer view-', 5, 0)
  buf = writeString(buf, 20, 11, 'port now auto-size to', 5, 0)
  buf = writeString(buf, 20, 12, 'fill their containers.', 5, 0)
  buf = writeString(buf, 0, 18, '='.repeat(c), 3, 0)
  buf = writeString(buf, 2, 19, 'Weather:  Sunny  22C  Wind: 12mph  Humidity: 45%', 7, 0)
  buf = writeString(buf, 2, 20, 'Sport:    Grid Editor Cup — Team Canvas leads 3-1', 3, 0)
  buf = writeString(buf, 0, r - 2, '='.repeat(c), 3, 0)
  buf = writeString(buf, 1, r - 1, 'uDosConnect  ·  uCode GridUI v3  ·  Ceefax Emulation', 7, 1)
  buf = writeString(buf, c - 10, r - 1, 'Page 100', 7, 1)
  activeCanvas.setBuffer(buf)
}

/* ─── Terminal Tab ────────────────────────────────────────────────── */
function terminalWebSocketUrl() {
  const url = new URL('/api/terminal/runtime/ws', UCORE_API)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url.toString()
}

function terminalPrintLine(text: string, fg = 7, bg = 0) {
  if (!activeCanvas) return
  const cfg = tabConfigs.terminal
  let buf = activeCanvas.buffer
  if (!buf || buf.length === 0) buf = createBuffer(cfg.cols, cfg.rows)
  if (terminalCursorY >= cfg.rows) { buf = scrollBuffer(buf, 1); terminalCursorY = cfg.rows - 1 }
  buf = writeString(buf, 0, terminalCursorY, text, fg, bg)
  terminalCursorX = 0
  terminalCursorY++
  activeCanvas.setBuffer(buf)
}

function terminalPutChar(char: string, fg = 7, bg = 0) {
  if (!activeCanvas) return
  const cfg = tabConfigs.terminal
  let buf = activeCanvas.buffer
  if (!buf || buf.length === 0) buf = createBuffer(cfg.cols, cfg.rows)
  if (terminalCursorY >= cfg.rows) { buf = scrollBuffer(buf, 1); terminalCursorY = cfg.rows - 1 }
  if (terminalCursorX >= cfg.cols) terminalNewLine()
  buf = activeCanvas.buffer || buf
  buf[terminalCursorY][terminalCursorX] = { char, fg, bg }
  terminalCursorX++
  activeCanvas.setBuffer(buf)
}

function terminalNewLine() {
  if (!activeCanvas) return
  const cfg = tabConfigs.terminal
  let buf = activeCanvas.buffer
  if (!buf || buf.length === 0) buf = createBuffer(cfg.cols, cfg.rows)
  terminalCursorX = 0
  terminalCursorY++
  if (terminalCursorY >= cfg.rows) { buf = scrollBuffer(buf, 1); terminalCursorY = cfg.rows - 1 }
  activeCanvas.setBuffer(buf)
}

function terminalBackspace() {
  if (!activeCanvas || terminalCursorX <= 0) return
  terminalCursorX--
  const buf = activeCanvas.buffer
  buf[terminalCursorY][terminalCursorX] = { char: ' ', fg: 7, bg: 0 }
  activeCanvas.setBuffer(buf)
}

function terminalClearScreen() {
  if (!activeCanvas) return
  const cfg = tabConfigs.terminal
  activeCanvas.setBuffer(createBuffer(cfg.cols, cfg.rows))
  terminalCursorX = 0
  terminalCursorY = 0
}

function terminalClearLineFromCursor() {
  if (!activeCanvas) return
  const cfg = tabConfigs.terminal
  const buf = activeCanvas.buffer
  for (let col = terminalCursorX; col < cfg.cols; col++) {
    buf[terminalCursorY][col] = { char: ' ', fg: 7, bg: 0 }
  }
  activeCanvas.setBuffer(buf)
}

function handleTerminalControlSequence(params: string, command: string) {
  if (command === 'H' || command === 'f') {
    const [row = '1', col = '1'] = params.split(';')
    terminalCursorY = Math.max(0, Number(row) - 1)
    terminalCursorX = Math.max(0, Number(col) - 1)
  } else if (command === 'J' && (params === '2' || params === '3')) {
    terminalClearScreen()
  } else if (command === 'K') {
    terminalClearLineFromCursor()
  }
}

function terminalWriteOutput(text: string) {
  let index = 0
  while (index < text.length) {
    if (text[index] === '\x1B' && text[index + 1] === ']') {
      const bellEnd = text.indexOf('\x07', index + 2)
      const stEnd = text.indexOf('\x1B\\', index + 2)
      const end = bellEnd >= 0 ? bellEnd + 1 : stEnd >= 0 ? stEnd + 2 : text.length
      index = end
      continue
    }
    if (text[index] === '\x1B' && text[index + 1] === '[') {
      const match = text.slice(index).match(/^\x1B\[([0-?]*)([ -/]*)([@-~])/)
      if (match) {
        handleTerminalControlSequence(match[1], match[3])
        index += match[0].length
        continue
      }
    }
    const char = text[index]
    if (char === '\r') terminalCursorX = 0
    else if (char === '\n') terminalNewLine()
    else if (char === '\b' || char === '\x7F') terminalBackspace()
    else if (char >= ' ') terminalPutChar(char)
    index++
  }
}

function loadTerminalWelcome() {
  if (!activeCanvas) return
  terminalCursorX = 0
  terminalCursorY = 0
  let buf = createBuffer(tabConfigs.terminal.cols, tabConfigs.terminal.rows)
  activeCanvas.setBuffer(buf)
  terminalPrintLine('uDosConnect Terminal Runtime', 4, 0)
  terminalPrintLine('='.repeat(tabConfigs.terminal.cols), 3, 0)
  terminalPrintLine('GridCore Canvas  ·  shell/PTY adapter', 2, 0)
  terminalPrintLine('Connecting to local runtime...', 7, 0)
  terminalPrintLine('', 7, 0)
  terminalCursorY = 6
}

function loadTerminalRuntime() {
  loadTerminalWelcome()
  connectTerminalRuntime()
}

function connectTerminalRuntime() {
  if (terminalSocket && terminalSocket.readyState <= WebSocket.OPEN) return
  try {
    terminalSocket = new WebSocket(terminalWebSocketUrl())
  } catch (err) {
    terminalPrintLine(`Runtime socket unavailable: ${String(err)}`, 1, 0)
    return
  }
  terminalSocket.addEventListener('open', () => {
    gridContainer.value?.focus()
  })
  terminalSocket.addEventListener('message', (event) => {
    try {
      const payload = JSON.parse(String(event.data))
      if (payload.type === 'ready') terminalPrintLine(`Runtime ready: ${payload.runtime}`, 2, 0)
      else if (payload.type === 'output') terminalWriteOutput(String(payload.data || ''))
      else if (payload.type === 'error') terminalPrintLine(String(payload.message || 'Runtime error'), 1, 0)
    } catch (err) {
      terminalPrintLine(`Runtime message error: ${String(err)}`, 1, 0)
    }
  })
  terminalSocket.addEventListener('close', () => {
    if (activeTab.value === 'terminal') terminalPrintLine('[runtime disconnected]', 3, 0)
    terminalSocket = null
  })
  terminalSocket.addEventListener('error', () => {
    terminalPrintLine('Runtime socket error; demo canvas remains available.', 1, 0)
  })
}

function disconnectTerminalRuntime() {
  if (!terminalSocket) return
  terminalSocket.close(1000, 'Terminal tab inactive')
  terminalSocket = null
}

function sendTerminalInput(data: string) {
  if (!terminalSocket || terminalSocket.readyState !== WebSocket.OPEN) return
  terminalSocket.send(JSON.stringify({ type: 'input', data }))
}

function onTerminalKeydown(event: KeyboardEvent) {
  if (activeTab.value !== 'terminal') return
  if (event.metaKey || event.ctrlKey || event.altKey) return
  if (event.key === 'Enter') { event.preventDefault(); sendTerminalInput('\r') }
  else if (event.key === 'Backspace') { event.preventDefault(); sendTerminalInput('\x7F') }
  else if (event.key === 'Tab') { event.preventDefault(); sendTerminalInput('\t') }
  else if (event.key.length === 1) { event.preventDefault(); sendTerminalInput(event.key) }
}

/* ─── Layer Tab ───────────────────────────────────────────────────── */
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
  activeCanvas.setBuffer(buf)
}

/* ─── Common ──────────────────────────────────────────────────────── */
function clearGrid() { activeCanvas?.clear() }
</script>

<style scoped>
/* ─── uCode shell chrome: compact USX controls around GridCore ───── */
.gridcore-surface {
  min-width: 0;
  overflow: hidden;
}

.gridcore-surface :deep(.surface-tab-nav) {
  min-width: 0;
  min-height: var(--gridcore-toolbar-min-height);
  padding: var(--gridcore-toolbar-padding-y) var(--gridcore-toolbar-padding-x);
  overflow-x: auto;
  scrollbar-width: thin;
}

.gridcore-surface :deep(button),
.gridcore-surface :deep(a) {
  box-shadow: none;
}

.gridcore-surface :deep(.surface-tab-nav__link) {
  min-height: var(--gridcore-toolbar-min-height);
  padding: var(--gridcore-space-xs) var(--gridcore-space-sm);
  gap: var(--gridcore-control-inline-gap);
  font-size: var(--gridcore-font-size-md);
  line-height: var(--gridcore-line-height-tight);
}

.gridcore-surface :deep(.surface-tab-nav__icon) {
  width: var(--gridcore-tool-btn-size);
  height: var(--gridcore-tool-btn-size);
  font-size: var(--gridcore-font-size-lg);
}

.gridcore-surface :deep(.surface-tab-nav__icon .material-symbols-outlined) {
  font-size: var(--gridcore-font-size-lg);
}

.gridcore-surface :deep(.surface-tab-nav__actions) {
  position: sticky;
  right: 0;
  gap: var(--gridcore-actions-gap);
  padding-left: var(--gridcore-space-sm);
  background: var(--gridcore-color-surface);
}

.gridcore-surface :deep(.surface-tab-nav__toggle) {
  width: var(--gridcore-tool-btn-size);
  height: var(--gridcore-tool-btn-size);
  padding: var(--gridcore-space-xs);
  font-size: var(--gridcore-font-size-lg);
}

/* ─── Single-canvas viewport ────────────────────────────────────── */
.ucode-viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 5%;
}
.ucode-viewport gridui-canvas { flex-shrink: 0; }

/* ─── Pixel Editor Layout ───────────────────────────────────────── */
.pixel-editor-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  gap: 0;
}

.pixel-editor-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.pixel-editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

/* ─── Pixel Toolbar (inside main content div) ───────────────────── */
.pixel-toolbar {
  display: flex;
  align-items: center;
  gap: var(--gridcore-toolbar-gap);
  padding: var(--gridcore-toolbar-padding-y) var(--gridcore-toolbar-padding-x);
  background: var(--gridcore-color-surface);
  border-bottom: var(--gridcore-border);
  border-radius: var(--gridcore-radius-md) var(--gridcore-radius-md) 0 0;
  flex-shrink: 0;
  min-height: var(--gridcore-toolbar-min-height);
  flex-wrap: nowrap;
}
.pixel-toolbar__dims {
  display: flex;
  align-items: center;
  gap: var(--gridcore-control-inline-gap);
}
.pixel-toolbar__label {
  font-size: var(--gridcore-font-size-xs);
  font-weight: var(--gridcore-font-weight-semibold);
  color: var(--gridcore-color-text-muted);
  text-transform: uppercase;
  height: var(--gridcore-control-height);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.pixel-toolbar__input {
  width: var(--gridcore-control-input-width);
  height: var(--gridcore-control-height);
  padding: 0 var(--gridcore-control-input-pad-x);
  font-size: var(--gridcore-font-size-sm);
  font-family: var(--gridcore-font-family-mono);
  background: var(--gridcore-color-background-alt);
  color: var(--gridcore-color-text);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-control-radius);
  text-align: center;
  line-height: var(--gridcore-control-height);
}
.pixel-toolbar__sep {
  font-size: var(--gridcore-font-size-md);
  color: var(--gridcore-color-text-muted);
  font-weight: var(--gridcore-font-weight-semibold);
  height: var(--gridcore-control-height);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}
.pixel-toolbar__palette {
  position: relative;
  display: flex;
  align-items: center;
  margin-left: auto;
  padding-left: var(--gridcore-control-divider-pad-left);
  border-left: var(--gridcore-border);
}

/* ─── Colour Picker Popover ─────────────────────────────────────── */
.pixel-colour-popover {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--gridcore-popover-offset-y);
  display: grid;
  grid-template-columns: repeat(3, var(--gridcore-popover-cell-size));
  grid-template-rows: repeat(3, var(--gridcore-popover-cell-size));
  gap: var(--gridcore-popover-gap);
  padding: var(--gridcore-popover-padding);
  background: var(--gridcore-color-surface);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-md);
  box-shadow: var(--gridcore-popover-shadow);
  z-index: 100;
}
.pixel-colour-popover__swatch {
  width: var(--gridcore-popover-cell-size);
  height: var(--gridcore-popover-cell-size);
  border-radius: var(--gridcore-popover-radius);
  border: var(--gridcore-border);
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}
.pixel-colour-popover__swatch:hover { border-color: var(--gridcore-color-text-muted); }
.pixel-colour-popover__swatch.fg-active { box-shadow: inset 0 0 0 var(--gridcore-active-ring-width) var(--gridcore-marker-fg-color); }
.pixel-colour-popover__swatch.bg-active { box-shadow: inset 0 0 0 var(--gridcore-active-ring-width) var(--gridcore-marker-bg-color); }
.pixel-colour-popover__swatch--empty {
  background-image: linear-gradient(45deg, var(--gridcore-checker-color) 25%, transparent 25%),
                    linear-gradient(-45deg, var(--gridcore-checker-color) 25%, transparent 25%),
                    linear-gradient(45deg, transparent 75%, var(--gridcore-checker-color) 75%),
                    linear-gradient(-45deg, transparent 75%, var(--gridcore-checker-color) 75%);
  background-size: var(--gridcore-checker-size) var(--gridcore-checker-size);
  background-position: 0 0, 0 calc(var(--gridcore-checker-size) / 2), calc(var(--gridcore-checker-size) / 2) calc(var(--gridcore-checker-size) / -2), calc(var(--gridcore-checker-size) / -2) 0;
}
.pixel-colour-popover__swatch--0,
.layer-colour-popover__swatch--0 { background: var(--gridcore-palette-0); }
.pixel-colour-popover__swatch--1,
.layer-colour-popover__swatch--1 { background: var(--gridcore-palette-1); }
.pixel-colour-popover__swatch--2,
.layer-colour-popover__swatch--2 { background: var(--gridcore-palette-2); }
.pixel-colour-popover__swatch--3,
.layer-colour-popover__swatch--3 { background: var(--gridcore-palette-3); }
.pixel-colour-popover__swatch--4,
.layer-colour-popover__swatch--4 { background: var(--gridcore-palette-4); }
.pixel-colour-popover__swatch--5,
.layer-colour-popover__swatch--5 { background: var(--gridcore-palette-5); }
.pixel-colour-popover__swatch--6,
.layer-colour-popover__swatch--6 { background: var(--gridcore-palette-6); }
.pixel-colour-popover__swatch--7,
.layer-colour-popover__swatch--7 { background: var(--gridcore-palette-7); }
.ucode-import-input { display: none; }
.pixel-colour-popover__swatch .colour-marker {
  position: absolute;
  font-size: var(--gridcore-marker-font-size);
  font-weight: var(--gridcore-font-weight-bold);
  line-height: 1;
  text-shadow: var(--gridcore-marker-shadow);
}
.pixel-colour-popover__swatch .colour-marker.fg { top: var(--gridcore-marker-offset-sm); left: var(--gridcore-marker-offset-md); color: var(--gridcore-marker-fg-color); }
.pixel-colour-popover__swatch .colour-marker.bg { bottom: var(--gridcore-marker-offset-sm); right: var(--gridcore-marker-offset-md); color: var(--gridcore-marker-bg-color); }
.pixel-toolbar__tools {
  display: flex;
  gap: var(--gridcore-control-inline-gap);
  padding: 0 var(--gridcore-control-segment-pad-x);
  border-left: var(--gridcore-border);
}
.pixel-toolbar__actions {
  display: flex;
  gap: var(--gridcore-actions-gap);
  margin-left: auto;
}
.pixel-tool-btn {
  width: var(--gridcore-tool-btn-size);
  height: var(--gridcore-tool-btn-size);
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: var(--gridcore-border);
  border-radius: var(--gridcore-popover-radius);
  color: var(--gridcore-color-text-muted);
  cursor: pointer;
  flex-shrink: 0;
}
.pixel-tool-btn:hover { color: var(--gridcore-color-text); background: var(--gridcore-color-background-alt); }
.pixel-tool-btn.active { color: var(--gridcore-color-primary); border-color: var(--gridcore-color-primary); background: var(--gridcore-color-background-alt); }
.pixel-toolbar__action-btn {
  height: var(--gridcore-action-btn-height);
  padding: 0 var(--gridcore-action-btn-pad-x);
  font-size: var(--gridcore-font-size-xs);
  font-weight: var(--gridcore-font-weight-semibold);
  background: var(--gridcore-color-background-alt);
  color: var(--gridcore-color-text-muted);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-popover-radius);
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  line-height: var(--gridcore-action-btn-height);
}
.pixel-toolbar__action-btn:hover { color: var(--gridcore-color-text); border-color: var(--gridcore-color-text-muted); }

.pixel-canvas-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: var(--gridcore-color-background-alt);
  border-radius: var(--gridcore-radius-md);
  outline: none;
  padding: var(--gridcore-space-md);
  flex: 1;
  align-self: stretch;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}
.pixel-canvas-wrapper:focus {
  outline: var(--gridcore-focus-outline-width) solid var(--gridcore-color-primary);
  outline-offset: var(--gridcore-focus-outline-offset);
}

/* ─── Grid Editor Layout ────────────────────────────────────────── */
.grid-editor-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  gap: 0;
  background: var(--gridcore-color-background);
}
.grid-editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  gap: 0;
}

/* ─── Layer Editor (primary pane) ────────────────────────────────── */
.layer-editor-primary {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  padding: var(--gridcore-space-sm);
  background: var(--gridcore-color-background);
}
.layer-editor__toolbar {
  display: flex;
  align-items: center;
  gap: var(--gridcore-toolbar-gap-lg);
  padding: var(--gridcore-toolbar-padding-y) var(--gridcore-toolbar-padding-x);
  flex-shrink: 0;
  border: var(--gridcore-border);
  border-bottom: none;
  border-radius: var(--gridcore-radius-md) var(--gridcore-radius-md) 0 0;
  background: var(--gridcore-color-surface);
  min-height: var(--gridcore-toolbar-min-height);
  flex-wrap: nowrap;
}
.layer-editor__dims {
  display: flex;
  align-items: center;
  gap: var(--gridcore-control-inline-gap);
}
.layer-editor__input {
  width: var(--gridcore-control-input-width);
  height: var(--gridcore-control-height);
  padding: 0 var(--gridcore-control-input-pad-x);
  font-size: var(--gridcore-font-size-sm);
  font-family: var(--gridcore-font-family-mono);
  background: var(--gridcore-color-background-alt);
  color: var(--gridcore-color-text);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-control-radius);
  text-align: center;
  line-height: var(--gridcore-control-height);
}
.layer-editor__sep {
  font-size: var(--gridcore-font-size-md);
  color: var(--gridcore-color-text-muted);
  font-weight: var(--gridcore-font-weight-semibold);
  height: var(--gridcore-control-height);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}
.layer-editor__tools {
  display: flex;
  gap: var(--gridcore-control-inline-gap);
  padding: 0 var(--gridcore-control-segment-pad-x);
  border-left: var(--gridcore-border);
}
.layer-editor__actions {
  display: flex;
  gap: var(--gridcore-actions-gap);
}
.layer-editor__palette {
  position: relative;
  display: flex;
  align-items: center;
  padding-left: var(--gridcore-control-divider-pad-left);
  border-left: var(--gridcore-border);
}
.layer-editor__info {
  margin-left: auto;
  font-size: var(--gridcore-font-size-sm);
  font-family: var(--gridcore-font-family-mono);
  color: var(--gridcore-color-text-muted);
  opacity: 0.7;
  white-space: nowrap;
}
.layer-editor__viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  background: var(--gridcore-color-background-alt);
  border: var(--gridcore-border);
  border-top: none;
  border-radius: 0 0 var(--gridcore-radius-md) var(--gridcore-radius-md);
  outline: none;
}
.layer-editor__viewport:focus {
  outline: var(--gridcore-focus-outline-width) solid var(--gridcore-color-primary);
  outline-offset: var(--gridcore-focus-outline-offset);
}

/* ─── Layer Colour Picker Popover ────────────────────────────────── */
.layer-colour-popover {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--gridcore-popover-offset-y);
  display: grid;
  grid-template-columns: repeat(3, var(--gridcore-popover-cell-size));
  grid-template-rows: repeat(3, var(--gridcore-popover-cell-size));
  gap: var(--gridcore-popover-gap);
  padding: var(--gridcore-popover-padding);
  background: var(--gridcore-color-surface);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-md);
  box-shadow: var(--gridcore-popover-shadow);
  z-index: 100;
}
.layer-colour-popover__swatch {
  width: var(--gridcore-popover-cell-size);
  height: var(--gridcore-popover-cell-size);
  border-radius: var(--gridcore-popover-radius);
  border: var(--gridcore-border);
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}
.layer-colour-popover__swatch:hover { border-color: var(--gridcore-color-text-muted); }
.layer-colour-popover__swatch.fg-active { box-shadow: inset 0 0 0 var(--gridcore-active-ring-width) var(--gridcore-marker-fg-color); }
.layer-colour-popover__swatch.bg-active { box-shadow: inset 0 0 0 var(--gridcore-active-ring-width) var(--gridcore-marker-bg-color); }
.layer-colour-popover__swatch--empty {
  background-image: linear-gradient(45deg, var(--gridcore-checker-color) 25%, transparent 25%),
                    linear-gradient(-45deg, var(--gridcore-checker-color) 25%, transparent 25%),
                    linear-gradient(45deg, transparent 75%, var(--gridcore-checker-color) 75%),
                    linear-gradient(-45deg, transparent 75%, var(--gridcore-checker-color) 75%);
  background-size: var(--gridcore-checker-size) var(--gridcore-checker-size);
  background-position: 0 0, 0 calc(var(--gridcore-checker-size) / 2), calc(var(--gridcore-checker-size) / 2) calc(var(--gridcore-checker-size) / -2), calc(var(--gridcore-checker-size) / -2) 0;
}
.layer-colour-popover__swatch .colour-marker {
  position: absolute;
  font-size: var(--gridcore-marker-font-size);
  font-weight: var(--gridcore-font-weight-bold);
  line-height: 1;
  text-shadow: var(--gridcore-marker-shadow);
}
.layer-colour-popover__swatch .colour-marker.bg { bottom: var(--gridcore-marker-offset-sm); right: var(--gridcore-marker-offset-md); color: var(--gridcore-marker-bg-color); }


/* ─── Sidebar ───────────────────────────────────────────────────── */
.editor-sidebar {
  width: var(--gridcore-sidebar-width);
  flex-shrink: 0;
  overflow-y: auto;
  border-left: var(--gridcore-border);
  background: var(--gridcore-color-surface);
  padding: var(--gridcore-sidebar-padding);
  display: flex;
  flex-direction: column;
  gap: var(--gridcore-space-md);
}
.sidebar-section { display: flex; flex-direction: column; gap: var(--gridcore-space-xs); }
.sidebar-title {
  font-size: var(--gridcore-sidebar-title-size); font-weight: var(--gridcore-font-weight-semibold); margin: 0;
  color: var(--gridcore-color-text-muted);
  text-transform: uppercase; letter-spacing: 0.08em;
}

/* Font mapping */
.sidebar-font-btns { display: flex; gap: var(--gridcore-sidebar-font-btn-gap); }
.sidebar-font-btn {
  flex: 1; padding: var(--gridcore-sidebar-font-btn-padding-y) var(--gridcore-space-xs);
  border: var(--gridcore-border);
  background: var(--gridcore-color-surface);
  color: var(--gridcore-color-text);
  cursor: pointer; border-radius: var(--gridcore-control-radius);
  font-size: var(--gridcore-sidebar-font-btn-size); font-family: var(--gridcore-font-family-mono);
  transition: background var(--gridcore-transition-fast), border-color var(--gridcore-transition-fast);
}
.sidebar-font-btn:hover { background: var(--gridcore-hover-bg); border-color: var(--gridcore-color-primary); }
.sidebar-font-btn.active { background: var(--gridcore-color-primary); color: var(--gridcore-color-on-primary); border-color: var(--gridcore-color-primary); }

/* Font character grid */
.sidebar-font-chars { flex: 1; min-height: 0; overflow-y: auto; }
.sidebar-chars-grid { display: grid; grid-template-columns: repeat(var(--gridcore-sidebar-char-columns), 1fr); gap: var(--gridcore-sidebar-char-gap); }
.sidebar-char-chip {
  display: flex; align-items: center; justify-content: center;
  width: 100%; aspect-ratio: 1;
  border: var(--gridcore-border);
  border-radius: var(--gridcore-sidebar-char-radius);
  background: var(--gridcore-color-surface);
  color: var(--gridcore-color-text);
  cursor: pointer;
  font-family: var(--gridcore-font-family-mono);
  font-size: var(--gridcore-sidebar-char-font-size);
  transition: background var(--gridcore-transition-fast), border-color var(--gridcore-transition-fast);
}
.sidebar-char-chip:hover { background: var(--gridcore-hover-bg); border-color: var(--gridcore-color-primary); }
.sidebar-char-chip.selected { border-color: var(--gridcore-color-primary); background: var(--gridcore-selection-bg); }

/* Canvas character preview */
.sidebar-char-preview {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: var(--gridcore-sidebar-preview-min-height);
  background: var(--gridcore-color-background-alt);
  border-radius: var(--gridcore-radius-sm);
  padding: var(--gridcore-space-xs);
  border: var(--gridcore-border);
}

/* Character input */
.sidebar-char-row { display: flex; gap: var(--gridcore-space-xs); align-items: center; }
.sidebar-char-input {
  width: var(--gridcore-sidebar-char-input-width); text-align: center; font-size: var(--gridcore-sidebar-char-input-size); font-family: var(--gridcore-font-family-mono);
  padding: var(--gridcore-space-xs);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-sm);
  background: var(--gridcore-color-surface);
  color: var(--gridcore-color-text);
}
.sidebar-char-code { font-size: var(--gridcore-font-size-xs); font-family: var(--gridcore-font-family-mono); color: var(--gridcore-color-text-muted); }

/* Colour markers */
.colour-marker {
  position: absolute; font-size: var(--gridcore-marker-font-size); font-weight: var(--gridcore-font-weight-bold); font-family: var(--gridcore-font-family-mono);
  line-height: 1; padding: var(--gridcore-marker-pad-y) var(--gridcore-marker-pad-x); border-radius: var(--gridcore-sidebar-char-radius); pointer-events: none;
}
.colour-marker.fg { top: var(--gridcore-marker-offset-sm); left: var(--gridcore-marker-offset-sm); background: var(--gridcore-marker-fg-bg); color: var(--gridcore-marker-fg-color); }
.colour-marker.bg { bottom: var(--gridcore-marker-offset-sm); right: var(--gridcore-marker-offset-sm); background: var(--gridcore-marker-bg-bg); color: var(--gridcore-marker-bg-color); }

/* Layer Composer prose stub */
.layer-composer-prose {
  max-width: var(--gridcore-prose-width);
  margin: var(--gridcore-space-xl) auto;
  padding: var(--gridcore-space-xl);
}
.layer-composer-prose h2 { font-size: var(--gridcore-prose-heading-size); margin: 0 0 var(--gridcore-space-md); color: var(--gridcore-color-text); }
.layer-composer-prose p { margin: 0 0 var(--gridcore-space-md); color: var(--gridcore-color-text); line-height: var(--gridcore-line-height-body); }
.layer-composer-prose ul { margin: 0; padding-left: var(--gridcore-space-lg); }
.layer-composer-prose a { color: var(--gridcore-color-primary); text-decoration: underline; }

/* ─── Shared ────────────────────────────────────────────────────── */
.ucode-info {
  font-size: var(--gridcore-font-size-sm);
  color: var(--gridcore-color-text-muted);
  font-family: var(--gridcore-font-family-mono);
  margin-left: var(--gridcore-space-xs);
  white-space: nowrap;
}
.surface-tab-nav__action-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: var(--gridcore-tool-btn-size); height: var(--gridcore-tool-btn-size);
  min-width: var(--gridcore-tool-btn-size); min-height: var(--gridcore-tool-btn-size);
  padding: 0;
  border: none; background: transparent;
  color: var(--gridcore-color-text-muted);
  cursor: pointer;
  border-radius: var(--gridcore-radius-sm);
  transition: color var(--gridcore-transition-fast), background var(--gridcore-transition-fast);
  -webkit-appearance: none; appearance: none; flex-shrink: 0;
}
.surface-tab-nav__action-btn:hover { color: var(--gridcore-color-primary); background: var(--gridcore-hover-bg); }
.surface-tab-nav__action-btn:active { color: var(--gridcore-color-primary-active); }
.surface-tab-nav__action-btn .u-icon { font-size: var(--gridcore-font-size-lg); }

/* ─── Viewport preset floating popover ────────────────────────── */
.ucode-actions-spacer { flex: 1; }
.surface__body, .surface__canvas, .grid-editor-layout, .pixel-editor-layout { position: relative; }
.preset-popover { position: absolute; top: 0; right: 0; left: auto; z-index: 10; max-height: 0; max-width: 100%; overflow: hidden; transition: max-height var(--gridcore-popover-transition); }
.preset-popover.open { max-height: var(--gridcore-preset-popover-max-height); }
.preset-popover__inner {
  display: flex; flex-direction: column; gap: var(--gridcore-preset-popover-gap);
  padding: var(--gridcore-space-xs);
  background: var(--gridcore-color-surface);
  border: var(--gridcore-border);
  border-radius: 0 0 var(--gridcore-radius-sm) var(--gridcore-radius-sm);
  box-shadow: var(--gridcore-preset-popover-shadow);
  min-width: var(--gridcore-preset-popover-min-width);
  max-width: 100%;
  max-height: var(--gridcore-preset-popover-max-height);
  overflow: auto;
}
.preset-popover__item {
  display: flex; align-items: center; justify-content: flex-end; gap: var(--gridcore-space-xs);
  width: 100%; padding: var(--gridcore-space-xs) var(--gridcore-space-sm);
  border: var(--gridcore-border-width) solid transparent; border-radius: var(--gridcore-radius-sm);
  background: transparent; color: var(--gridcore-color-text);
  cursor: pointer; font-size: var(--gridcore-font-size-sm); font-family: var(--gridcore-font-family-mono);
  white-space: nowrap; text-align: right;
  transition: background var(--gridcore-transition-fast), border-color var(--gridcore-transition-fast);
}
.preset-popover__item:hover { background: var(--gridcore-hover-bg); border-color: var(--gridcore-color-primary); }
.preset-popover__item.active { border-color: var(--gridcore-color-primary); background: var(--gridcore-selection-bg-muted); }
.preset-popover__dims { font-weight: var(--gridcore-font-weight-semibold); }
.preset-popover__desc { color: var(--gridcore-color-text-muted); }

@media (max-width: 50em) {
  .gridcore-surface :deep(.surface-tab-nav__label) {
    display: none;
  }

  .gridcore-surface :deep(.surface-tab-nav__link) {
    min-width: var(--gridcore-tool-btn-size);
    justify-content: center;
  }

  .preset-popover__item {
    justify-content: flex-start;
    text-align: left;
  }
}
</style>