<template>
  <div
    class="gridcore-ui"
    :class="[`gridcore-ui--${mode}`, `gridcore-ui--${cols}x${rows}`]"
    :style="gridStyle"
  >
    <div ref="gridContainer" class="gridcore-ui__viewport" role="region" :aria-label="ariaLabel">
    </div>
    <div v-if="mode === 'edit'" class="gridcore-ui__status">
      <span class="gridcore-ui__info">{{ cols }}×{{ rows }}</span>
      <span v-if="hoveredCell" class="gridcore-ui__cell-info">
        ({{ hoveredCell.col }}, {{ hoveredCell.row }})
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * GridCoreUI — Embeddable Grid Display Component
 *
 * A Vue component wrapper around the <gridui-canvas> Web Component.
 * Supports view, edit, and map modes.
 *
 * Usage:
 *   <GridCoreUI :buffer="myBuffer" :cols="60" :rows="20" mode="view" />
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  createGridUICanvas,
  type GridUICanvasElement,
} from './gridui-canvas'
import type { GridBuffer, GridMode } from './types'

const props = withDefaults(defineProps<{
  buffer?: GridBuffer
  cols?: number
  rows?: number
  cellSize?: number
  font?: string
  mode?: GridMode
}>(), {
  cols: 40,
  rows: 25,
  cellSize: 16,
  font: 'monospace',
  mode: 'view',
})

const emit = defineEmits<{
  'cell-click': [cell: { col: number; row: number }]
  'cell-hover': [cell: { col: number; row: number } | null]
}>()

const gridContainer = ref<HTMLDivElement>()
let gridEl: GridUICanvasElement | null = null
const hoveredCell = ref<{ col: number; row: number } | null>(null)

const gridStyle = computed(() => ({
  '--grid-cols': props.cols,
  '--grid-rows': props.rows,
  '--grid-cell-size': `${props.cellSize}px`,
}))

const ariaLabel = computed(() =>
  `Grid display: ${props.cols} columns by ${props.rows} rows, ${props.mode} mode`
)

onMounted(() => {
  if (!gridContainer.value) return
  gridEl = createGridUICanvas({
    cols: props.cols,
    rows: props.rows,
    cellSize: props.cellSize,
    font: props.font,
  })
  gridContainer.value.appendChild(gridEl)

  // Forward events
  gridEl.addEventListener('cell-click', ((e: CustomEvent) => {
    emit('cell-click', e.detail)
  }) as EventListener)

  gridEl.addEventListener('cell-hover', ((e: CustomEvent) => {
    hoveredCell.value = e.detail
    emit('cell-hover', e.detail)
  }) as EventListener)

  // Set initial buffer
  if (props.buffer) {
    gridEl.setBuffer(props.buffer)
  }
})

onUnmounted(() => {
  gridEl?.remove()
  gridEl = null
})

// Watch for buffer changes
watch(() => props.buffer, (newBuf) => {
  if (gridEl && newBuf) {
    gridEl.setBuffer(newBuf)
  }
}, { deep: true })

// Expose setBuffer for parent components
defineExpose({
  setBuffer(buf: GridBuffer) {
    if (gridEl) gridEl.setBuffer(buf)
  },
  clear() {
    if (gridEl) gridEl.clear()
  },
})
</script>

<style scoped>
.gridcore-ui {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  height: 100%;
}

.gridcore-ui__viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  min-height: 0;
}

.gridcore-ui__status {
  display: flex;
  justify-content: space-between;
  padding: 2px 8px;
  font-family: monospace;
  font-size: 11px;
  color: var(--usx-color-on-surface-muted);
  background: rgba(0, 0, 0, 0.3);
  border-radius: 2px;
}

.gridcore-ui__info {
  font-weight: 600;
}

.gridcore-ui__cell-info {
  color: var(--usx-color-primary);
}
</style>
