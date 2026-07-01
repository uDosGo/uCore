/**
 * @module gridui-canvas
 * @description Framework-agnostic embeddable grid widget for uCore.
 *
 * Architecture:
 *   GridBuffer (data) → GridUICanvasElement (Web Component) → DOM <span> grid
 *
 * Usage (HTML):
 *   <gridui-canvas cols="80" rows="24"></gridui-canvas>
 *
 * Usage (JS):
 *   import { createGridUICanvas, textToGridBuffer } from './vendor/gridui-canvas'
 *   const el = createGridUICanvas({ cols: 40, rows: 12 })
 *   el.setBuffer(textToGridBuffer('Hello World', 40))
 *   document.body.appendChild(el)
 *
 * Usage (Vue):
 *   <template><div ref="grid"></div></template>
 *   <script setup>
 *   import { createGridUICanvas } from '@/vendor/gridui-canvas'
 *   onMounted(() => {
 *     const el = createGridUICanvas({ cols: 80, rows: 24 })
 *     grid.value.appendChild(el)
 *   })
 *   </script>
 *
 * No React, no Vue, no framework deps in this package.
 * The Web Component registers itself as <gridui-canvas> on import.
 */
export {
  GridUICanvasElement,
  createGridUICanvas,
  textToGridBuffer,
  type GridUICanvasConfig,
} from './GridUICanvasElement'

// Re-export all grid-algebra types and functions
export * from './grid-algebra/index'
