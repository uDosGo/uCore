<template>
  <div
    class="multi-column-viewer"
    :style="{
      gridTemplateColumns: `repeat(${spec.count}, minmax(0, ${spec.width}))`,
      gap: spec.gap
    }"
  >
    <div
      v-for="(slide, index) in slides"
      :key="index"
      class="multi-column-viewer__column"
    >
      <div class="multi-column-viewer__content" v-html="slide"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * MultiColumnViewer — Multi-Column Layout View
 *
 * Renders markdown slides (separated by ---) side-by-side in columns.
 * Column count auto-resolves via Grid Algebra based on viewport width:
 *   <480px: 1 col   480-768: 2 cols   768-1024: 2 cols
 *   1024-1440: 3 cols   1440-1920: 3 cols   1920+: 4 cols
 *
 * Each column enforces the ch-based width from the spec.
 *
 * Usage:
 *   <MultiColumnViewer :source="markdownString" />
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { renderSlides, renderMarkdown } from '../composables/useMarkdown'
import { resolveColumns } from './algebra'
import type { ColumnSpec } from './types'

const props = defineProps<{
  source: string
}>()

const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)
const spec = ref<ColumnSpec>(resolveColumns(viewportWidth.value))

const slides = computed(() => {
  const { slides } = renderSlides(props.source)
  return slides.map(s => renderMarkdown(s))
})

function onResize() {
  viewportWidth.value = window.innerWidth
  spec.value = resolveColumns(viewportWidth.value)
}

onMounted(() => {
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.multi-column-viewer {
  display: grid;
  padding: var(--usx-spacing-xl, 24px);
  height: 100%;
  overflow: hidden;
  justify-content: center;
}

.multi-column-viewer__column {
  overflow-y: auto;
  padding: var(--usx-spacing-lg, 16px);
  background: var(--pico-card-background-color, #0d1117);
  border: 1px solid var(--pico-border-color, #30363d);
  border-radius: var(--usx-border-radius-md, 6px);
}

.multi-column-viewer__content {
  font-size: 0.9em;
  line-height: 1.6;
  color: var(--pico-color, #c2c7d0);
}

.multi-column-viewer__content :deep(h1),
.multi-column-viewer__content :deep(h2),
.multi-column-viewer__content :deep(h3) {
  margin-top: 0;
  margin-bottom: 0.5em;
  font-weight: 600;
}

.multi-column-viewer__content :deep(h1) { font-size: 1.5em; }
.multi-column-viewer__content :deep(h2) { font-size: 1.25em; }
.multi-column-viewer__content :deep(h3) { font-size: 1.1em; }

.multi-column-viewer__content :deep(p) {
  margin-bottom: 0.75em;
}

.multi-column-viewer__content :deep(a) {
  color: var(--pico-primary, #58a6ff);
}

.multi-column-viewer__content :deep(code) {
  background: var(--pico-code-background-color, #1a2332);
  padding: 0.15em 0.3em;
  border-radius: 3px;
  font-size: 0.85em;
}

.multi-column-viewer__content :deep(pre) {
  background: var(--pico-code-background-color, #1a2332);
  padding: var(--usx-spacing-md, 12px);
  border-radius: var(--usx-border-radius-sm, 4px);
  overflow-x: auto;
  margin-bottom: 0.75em;
}

.multi-column-viewer__content :deep(blockquote) {
  border-left: 2px solid var(--pico-primary, #58a6ff);
  padding-left: var(--usx-spacing-md, 12px);
  margin-left: 0;
  color: var(--pico-muted-color, #8b949e);
}

.multi-column-viewer__content :deep(ul),
.multi-column-viewer__content :deep(ol) {
  padding-left: 1.25em;
  margin-bottom: 0.75em;
}

.multi-column-viewer__content :deep(li) {
  margin-bottom: 0.2em;
}
</style>
