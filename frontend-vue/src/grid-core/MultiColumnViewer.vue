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
  padding: var(--gridcore-viewer-padding);
  height: 100%;
  overflow: hidden;
  justify-content: center;
}

.multi-column-viewer__column {
  overflow-y: auto;
  padding: var(--gridcore-viewer-column-padding);
  background: var(--gridcore-color-surface);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-md);
}

.multi-column-viewer__content {
  font-size: var(--gridcore-font-size-body);
  line-height: var(--gridcore-line-height-body);
  color: var(--gridcore-color-text);
}

.multi-column-viewer__content :deep(h1),
.multi-column-viewer__content :deep(h2),
.multi-column-viewer__content :deep(h3) {
  margin-top: 0;
  margin-bottom: var(--gridcore-viewer-margin-sm);
  font-weight: var(--gridcore-font-weight-semibold);
}

.multi-column-viewer__content :deep(h1) { font-size: 1.5em; }
.multi-column-viewer__content :deep(h2) { font-size: 1.25em; }
.multi-column-viewer__content :deep(h3) { font-size: 1.1em; }

.multi-column-viewer__content :deep(p) {
  margin-bottom: var(--gridcore-viewer-margin-md);
}

.multi-column-viewer__content :deep(a) {
  color: var(--gridcore-color-primary);
}

.multi-column-viewer__content :deep(code) {
  background: var(--gridcore-color-surface-muted);
  padding: var(--gridcore-viewer-code-padding-y) var(--gridcore-viewer-code-padding-x);
  border-radius: var(--gridcore-control-radius);
  font-size: var(--gridcore-font-size-code);
}

.multi-column-viewer__content :deep(pre) {
  background: var(--gridcore-color-surface-muted);
  padding: var(--gridcore-space-md);
  border-radius: var(--gridcore-radius-sm);
  overflow-x: auto;
  margin-bottom: var(--gridcore-viewer-margin-md);
}

.multi-column-viewer__content :deep(blockquote) {
  border-left: var(--gridcore-viewer-blockquote-width) solid var(--gridcore-color-primary);
  padding-left: var(--gridcore-viewer-blockquote-pad-left);
  margin-left: 0;
  color: var(--gridcore-color-text-muted);
}

.multi-column-viewer__content :deep(ul),
.multi-column-viewer__content :deep(ol) {
  padding-left: 1.25em;
  margin-bottom: var(--gridcore-viewer-margin-md);
}

.multi-column-viewer__content :deep(li) {
  margin-bottom: 0.2em;
}
</style>
