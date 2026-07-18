<template>
  <span
    class="u-badge"
    :class="[
      `u-badge--${type}`,
      `u-badge--${size}`,
      { 'u-badge--circle': circle, 'u-badge--pill': pill }
    ]"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
/**
 * @component UBadge
 * @description Status badge with semantic color variants.
 * - Default: solid semantic fill
 * - circle: filled circle (tight, equal w/h, inverted colours)
 * - pill: filled pill shape (Bootstrap-style)
 * @category atoms
 * @props {'info' | 'success' | 'warning' | 'error'} type - Badge color variant
 * @props {boolean} circle - Makes badge a perfect circle with filled colours
 * @props {boolean} pill - Filled pill shape (Bootstrap-style)
 * @usage <UBadge type="info">3</UBadge>
 * @usage <UBadge type="info" circle>3</UBadge>
 * @usage <UBadge type="success" pill>Active</UBadge>
 */

interface Props {
  type?: 'info' | 'success' | 'warning' | 'error'
  size?: 'sm' | 'md'
  circle?: boolean
  pill?: boolean
}

withDefaults(defineProps<Props>(), {
  type: 'info',
  size: 'md',
  circle: false,
  pill: false,
})
</script>

<style scoped>
.u-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border-radius: var(--usx-radius-full);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  line-height: var(--usx-line-height-tight);
  white-space: nowrap;
  min-height: 1.5em;
  box-sizing: border-box;
  border: var(--usx-border-width) solid transparent;
  flex-shrink: 0;
}

.u-badge--sm {
  padding: var(--usx-spacing-1) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
}

.u-badge--md {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
}

/* ─── Circle variant — tight, equal w/h, filled colours ───────── */
.u-badge--circle {
  padding: 0;
  width: 1.8em;
  height: 1.8em;
  min-width: 1.8em;
  min-height: 1.8em;
  border-radius: 50%;
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-none);
  letter-spacing: 0;
}

/* ─── Pill variant — Bootstrap-style filled pill ──────────────── */
.u-badge--pill {
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  font-weight: var(--usx-font-weight-medium);
  letter-spacing: 0.02em;
  line-height: var(--usx-line-height-tight);
}

/* ─── Solid variants (default) ─────────────────────────────────── */
.u-badge--info {
  background: var(--usx-color-info);
  border-color: transparent;
  color: var(--usx-color-on-info);
}

.u-badge--success {
  background: var(--usx-color-success);
  border-color: transparent;
  color: var(--usx-color-on-success);
}

.u-badge--warning {
  background: var(--usx-color-warning);
  border-color: transparent;
  color: var(--usx-color-on-warning);
}

.u-badge--error {
  background: var(--usx-color-danger);
  border-color: transparent;
  color: var(--usx-color-on-danger);
}
</style>
