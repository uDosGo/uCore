<template>
  <div class="prose-viewer" :style="{ maxWidth: proseMaxWidth }">
    <div class="prose-viewer__content" v-html="html"></div>
  </div>
</template>

<script setup lang="ts">
/**
 * ProseViewer — Standard Prose Reading View
 *
 * Renders markdown as a traditional scrolling document using
 * responsive column widths via the Grid Algebra.
 * Slide separators (---) are automatically stripped.
 *
 * The column width auto-resolves based on viewport width:
 *   <480px:  1×40ch  480px: 2×35ch  768px: 2×40ch
 *   1024px: 3×35ch  1440px: 3×40ch  1920px+: 4×40ch
 *
 * Usage:
 *   <ProseViewer :source="markdownString" />
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { renderMarkdown } from '../composables/useMarkdown'
import { resolveColumns } from './algebra'
import type { ColumnSpec } from './types'

const props = defineProps<{
  source: string
}>()

const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)
const spec = ref<ColumnSpec>(resolveColumns(viewportWidth.value))

const html = computed(() => renderMarkdown(props.source))

const proseMaxWidth = computed(() => {
  const s = spec.value
  return s.count === 1 ? s.width : s.maxWidth
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
.prose-viewer {
  margin: 0 auto;
  padding: var(--usx-spacing-xl, 24px);
  line-height: var(--usx-line-height-relaxed, 1.8);
  color: var(--pico-color, #c2c7d0);
  width: 100%;
}

.prose-viewer__content {
  width: 100%;
}

.prose-viewer__content :deep(h1),
.prose-viewer__content :deep(h2),
.prose-viewer__content :deep(h3),
.prose-viewer__content :deep(h4) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.3;
}

.prose-viewer__content :deep(h1) { font-size: 2em; }
.prose-viewer__content :deep(h2) { font-size: 1.5em; }
.prose-viewer__content :deep(h3) { font-size: 1.25em; }
.prose-viewer__content :deep(h4) { font-size: 1.1em; }

.prose-viewer__content :deep(p) {
  margin-bottom: 1em;
}

.prose-viewer__content :deep(a) {
  color: var(--pico-primary, #58a6ff);
  text-decoration: none;
}

.prose-viewer__content :deep(a:hover) {
  text-decoration: underline;
}

.prose-viewer__content :deep(code) {
  background: var(--pico-code-background-color, #1a2332);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}

.prose-viewer__content :deep(pre) {
  background: var(--pico-code-background-color, #1a2332);
  padding: var(--usx-spacing-lg, 16px);
  border-radius: var(--usx-border-radius-md, 6px);
  overflow-x: auto;
  margin-bottom: 1em;
}

.prose-viewer__content :deep(pre code) {
  background: none;
  padding: 0;
}

.prose-viewer__content :deep(blockquote) {
  border-left: 3px solid var(--pico-primary, #58a6ff);
  padding-left: var(--usx-spacing-lg, 16px);
  margin-left: 0;
  color: var(--pico-muted-color, #8b949e);
}

.prose-viewer__content :deep(ul),
.prose-viewer__content :deep(ol) {
  padding-left: 1.5em;
  margin-bottom: 1em;
}

.prose-viewer__content :deep(li) {
  margin-bottom: 0.25em;
}

.prose-viewer__content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1em;
}

.prose-viewer__content :deep(th),
.prose-viewer__content :deep(td) {
  padding: 0.5em 0.75em;
  border: 1px solid var(--pico-border-color, #30363d);
  text-align: left;
}

.prose-viewer__content :deep(th) {
  background: var(--pico-card-sectioning-background-color, #161b22);
  font-weight: 600;
}

.prose-viewer__content :deep(hr) {
  border: none;
  border-top: 1px solid var(--pico-border-color, #30363d);
  margin: 2em 0;
}
</style>
