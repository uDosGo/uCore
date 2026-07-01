<template>
  <div class="slide-viewer" :class="[`slide-viewer--${aspect}`]">
    <div class="slide-viewer__navigation" v-if="slides.length > 1">
      <button class="slide-viewer__nav-btn" @click="prevSlide" :disabled="currentIndex === 0">
        ← Prev
      </button>
      <span class="slide-viewer__counter">{{ currentIndex + 1 }} / {{ slides.length }}</span>
      <button class="slide-viewer__nav-btn" @click="nextSlide" :disabled="currentIndex === slides.length - 1">
        Next →
      </button>
    </div>
    <div class="slide-viewer__stage">
      <div
        class="slide-viewer__slide"
        v-html="currentSlideHTML"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * SlideViewer — Marp-Style Slide Presentation View
 *
 * Renders markdown slides (separated by ---) as a full-screen
 * presentation with navigation controls.
 *
 * Usage:
 *   <SlideViewer :source="markdownString" aspect="16:9" />
 */
import { computed, ref } from 'vue'
import { renderSlides, renderMarkdown } from '../composables/useMarkdown'


const props = withDefaults(defineProps<{
  source: string
  aspect?: '16:9' | '4:3' | 'fill'
}>(), {
  aspect: '16:9',
})

const slides = computed(() => {
  const { slides } = renderSlides(props.source)
  return slides
})

const currentIndex = ref(0)

const currentSlideHTML = computed(() => {
  if (slides.value.length === 0) return ''
  return renderMarkdown(slides.value[currentIndex.value])
})

function nextSlide() {
  if (currentIndex.value < slides.value.length - 1) {
    currentIndex.value++
  }
}

function prevSlide() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

// Keyboard navigation
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', (e: KeyboardEvent) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      nextSlide()
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      prevSlide()
    }
  })
}
</script>

<style scoped>
.slide-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: var(--pico-background-color, #0d1117);
}

.slide-viewer__navigation {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-lg, 16px);
  padding: var(--usx-spacing-md, 12px);
  background: var(--pico-card-background-color, #161b22);
  border-bottom: 1px solid var(--pico-border-color, #30363d);
}

.slide-viewer__nav-btn {
  padding: 6px 16px;
  border: 1px solid var(--pico-border-color, #30363d);
  border-radius: var(--usx-border-radius-sm, 4px);
  background: var(--pico-card-background-color, #0d1117);
  color: var(--pico-color, #c2c7d0);
  cursor: pointer;
  font-size: 0.9em;
}

.slide-viewer__nav-btn:hover:not(:disabled) {
  background: var(--pico-primary-hover-background, #1f6feb);
  color: #fff;
}

.slide-viewer__nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.slide-viewer__counter {
  font-family: monospace;
  font-size: 0.85em;
  color: var(--pico-muted-color, #8b949e);
}

.slide-viewer__stage {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: var(--usx-spacing-xl, 24px);
}

.slide-viewer__slide {
  width: 100%;
  max-width: 960px;
  padding: var(--usx-spacing-2xl, 48px);
  background: var(--pico-card-background-color, #0d1117);
  border: 1px solid var(--pico-border-color, #30363d);
  border-radius: var(--usx-border-radius-lg, 8px);
  line-height: 1.6;
  color: var(--pico-color, #c2c7d0);
}

.slide-viewer--16-9 .slide-viewer__slide {
  aspect-ratio: 16 / 9;
}

.slide-viewer--4-3 .slide-viewer__slide {
  aspect-ratio: 4 / 3;
}

.slide-viewer--fill .slide-viewer__slide {
  aspect-ratio: auto;
  min-height: 60vh;
}

.slide-viewer__slide :deep(h1) {
  font-size: 2.5em;
  margin-bottom: 0.5em;
  text-align: center;
}

.slide-viewer__slide :deep(h2) {
  font-size: 1.75em;
  margin-bottom: 0.5em;
}

.slide-viewer__slide :deep(p) {
  font-size: 1.1em;
  margin-bottom: 0.75em;
}

.slide-viewer__slide :deep(ul),
.slide-viewer__slide :deep(ol) {
  font-size: 1.1em;
  padding-left: 1.5em;
}

.slide-viewer__slide :deep(code) {
  background: var(--pico-code-background-color, #1a2332);
  padding: 0.2em 0.4em;
  border-radius: 3px;
}

.slide-viewer__slide :deep(pre) {
  background: var(--pico-code-background-color, #1a2332);
  padding: var(--usx-spacing-lg, 16px);
  border-radius: var(--usx-border-radius-md, 6px);
  overflow-x: auto;
}

.slide-viewer__slide :deep(blockquote) {
  border-left: 3px solid var(--pico-primary, #58a6ff);
  padding-left: var(--usx-spacing-lg, 16px);
  margin-left: 0;
  color: var(--pico-muted-color, #8b949e);
}

.slide-viewer__slide :deep(img) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}
</style>
