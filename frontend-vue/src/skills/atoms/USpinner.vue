<template>
  <div class="u-spinner" :style="spinnerStyle">
    <div class="u-spinner__ring" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
/**
 * @component USpinner
 * @description Loading spinner with configurable size.
 * @category atoms
 * @props {number} size - Spinner diameter in pixels
 * @usage <USpinner :size="24" />
 */

interface Props {
  size?: number
}

const props = withDefaults(defineProps<Props>(), {
  size: 20,
})

const spinnerStyle = computed(() => ({
  '--u-spinner-size': `${props.size}px`,
}))
</script>

<style scoped>
.u-spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--u-spinner-size);
  height: var(--u-spinner-size);
}

.u-spinner__ring {
  width: 100%;
  height: 100%;
  border: var(--usx-border-width-thick) solid var(--usx-color-border);
  border-top-color: var(--usx-color-primary);
  border-radius: 50%;
  animation: spinner-rotate var(--usx-motion-duration-slow) linear infinite;
}

@keyframes spinner-rotate {
  to { transform: rotate(360deg); }
}
</style>
