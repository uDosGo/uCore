<template>
  <div class="u-spinner" :style="{ width: `${size}px`, height: `${size}px` }">
    <div class="u-spinner__ring" />
  </div>
</template>

<script setup lang="ts">
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

withDefaults(defineProps<Props>(), {
  size: 20,
})
</script>

<style scoped>
.u-spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.u-spinner__ring {
  width: 100%;
  height: 100%;
  border: 2px solid var(--usx-color-border);
  border-top-color: var(--usx-color-primary);
  border-radius: 50%;
  animation: spinner-rotate 0.6s linear infinite;
}

@keyframes spinner-rotate {
  to { transform: rotate(360deg); }
}
</style>
