<template>
  <span class="u-badge" :class="`u-badge--${type}`">
    <slot />
  </span>
</template>

<script setup lang="ts">
/**
 * @component UBadge
 * @description Status badge with semantic color variants.
 * @category atoms
 * @props {'info' | 'success' | 'warning' | 'error'} type - Badge color variant
 * @usage <UBadge type="success">Running</UBadge>
 */

interface Props {
  type?: 'info' | 'success' | 'warning' | 'error'
}

withDefaults(defineProps<Props>(), {
  type: 'info',
})
</script>

<style scoped>
.u-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--usx-badge-padding-vertical) var(--usx-badge-padding-horizontal);
  border-radius: var(--usx-border-radius-full);
  font-size: var(--usx-font-size-sm);
  font-weight: 500;
  line-height: 1.4;
}

.u-badge--info {
  background: var(--pico-background-color);
  color: #58a6ff;
}

.u-badge--success {
  background: var(--pico-background-color);
  color: #2ea043;
}

.u-badge--warning {
  background: var(--pico-background-color);
  color: #d29922;
}

.u-badge--error {
  background: rgba(248, 81, 73, 0.15);
  color: #f85149;
}
</style>
