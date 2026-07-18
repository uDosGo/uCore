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
  background: var(--gridcore-color-background);
}

.slide-viewer__navigation {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--gridcore-space-lg);
  padding: var(--gridcore-space-md);
  background: var(--gridcore-color-surface);
  border-bottom: var(--gridcore-border);
}

.slide-viewer__nav-btn {
  padding: var(--gridcore-slide-nav-padding-y) var(--gridcore-slide-nav-padding-x);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-sm);
  background: var(--gridcore-color-background-alt);
  color: var(--gridcore-color-text);
  cursor: pointer;
  font-size: var(--gridcore-font-size-body);
}

.slide-viewer__nav-btn:hover:not(:disabled) {
  background: var(--gridcore-color-primary-hover);
  color: var(--gridcore-color-on-primary);
}

.slide-viewer__nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.slide-viewer__counter {
  font-family: var(--gridcore-font-family-mono);
  font-size: var(--gridcore-font-size-code);
  color: var(--gridcore-color-text-muted);
}

.slide-viewer__stage {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: var(--gridcore-viewer-padding);
}

.slide-viewer__slide {
  width: 100%;
  max-width: var(--gridcore-slide-max-width);
  padding: var(--gridcore-space-2xl);
  background: var(--gridcore-color-background-alt);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-lg);
  line-height: var(--gridcore-line-height-body);
  color: var(--gridcore-color-text);
}

.slide-viewer--16-9 .slide-viewer__slide {
  aspect-ratio: 16 / 9;
}

.slide-viewer--4-3 .slide-viewer__slide {
  aspect-ratio: 4 / 3;
}

.slide-viewer--fill .slide-viewer__slide {
  aspect-ratio: auto;
  min-height: var(--gridcore-slide-min-height);
}

.slide-viewer__slide :deep(h1) {
  font-size: var(--gridcore-slide-h1-size);
  margin-bottom: var(--gridcore-viewer-margin-sm);
  text-align: center;
}

.slide-viewer__slide :deep(h2) {
  font-size: var(--gridcore-slide-h2-size);
  margin-bottom: var(--gridcore-viewer-margin-sm);
}

.slide-viewer__slide :deep(p) {
  font-size: var(--gridcore-slide-body-size);
  margin-bottom: var(--gridcore-viewer-margin-md);
}

.slide-viewer__slide :deep(ul),
.slide-viewer__slide :deep(ol) {
  font-size: var(--gridcore-slide-body-size);
  padding-left: var(--gridcore-viewer-list-pad-left);
}

.slide-viewer__slide :deep(code) {
  background: var(--gridcore-color-surface-muted);
  padding: var(--gridcore-marker-pad-x) calc(var(--gridcore-marker-pad-x) * 2);
  border-radius: var(--gridcore-control-radius);
}

.slide-viewer__slide :deep(pre) {
  background: var(--gridcore-color-surface-muted);
  padding: var(--gridcore-space-lg);
  border-radius: var(--gridcore-radius-md);
  overflow-x: auto;
}

.slide-viewer__slide :deep(blockquote) {
  border-left: calc(var(--gridcore-viewer-blockquote-width) + var(--gridcore-border-width)) solid var(--gridcore-color-primary);
  padding-left: var(--gridcore-space-lg);
  margin-left: 0;
  color: var(--gridcore-color-text-muted);
}

.slide-viewer__slide :deep(img) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}
</style>
