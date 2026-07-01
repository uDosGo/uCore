<template>
  <span class="u-badge" :class="[`u-badge--${type}`, { 'u-badge--circle': circle, 'u-badge--pill': pill }]">
    <slot />
  </span>
</template>

<script setup lang="ts">
/**
 * @component UBadge
 * @description Status badge with semantic color variants.
 * - Default: outline style with tinted border + text
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
  circle?: boolean
  pill?: boolean
}

withDefaults(defineProps<Props>(), {
  type: 'info',
  circle: false,
  pill: false,
})
</script>

<style scoped>
.u-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  line-height: 1;
  min-width: 1.5em;
  min-height: 1.5em;
  box-sizing: border-box;
}

/* ─── Circle variant — tight, equal w/h, filled colours ───────── */
.u-badge--circle {
  padding: 0;
  width: 1.5em;
  height: 1.5em;
  border-radius: 50%;
  font-size: var(--usx-font-size-xs);
  line-height: 1;
}

/* ─── Pill variant — Bootstrap-style filled pill ──────────────── */
.u-badge--pill {
  padding: 3px var(--usx-spacing-md);
  border: none;
  font-weight: var(--usx-font-weight-medium);
  letter-spacing: 0.02em;
}

/* ─── Outline (default) ────────────────────────────────────────── */
.u-badge--info {
  background: transparent;
  border: var(--usx-border-width) solid var(--usx-color-info);
  color: var(--usx-color-info);
}

.u-badge--info.u-badge--circle,
.u-badge--info.u-badge--pill {
  background: var(--usx-color-info);
  border: none;
  color: var(--usx-color-on-info);
}

.u-badge--success {
  background: transparent;
  border: var(--usx-border-width) solid var(--usx-color-success);
  color: var(--usx-color-success);
}

.u-badge--success.u-badge--circle,
.u-badge--success.u-badge--pill {
  background: var(--usx-color-success);
  border: none;
  color: var(--usx-color-on-success);
}

.u-badge--warning {
  background: transparent;
  border: var(--usx-border-width) solid var(--usx-color-warning);
  color: var(--usx-color-warning);
}

.u-badge--warning.u-badge--circle,
.u-badge--warning.u-badge--pill {
  background: var(--usx-color-warning);
  border: none;
  color: var(--usx-color-on-warning);
}

.u-badge--error {
  background: transparent;
  border: var(--usx-border-width) solid var(--usx-color-danger);
  color: var(--usx-color-danger);
}

.u-badge--error.u-badge--circle,
.u-badge--error.u-badge--pill {
  background: var(--usx-color-danger);
  border: none;
  color: var(--usx-color-on-danger);
}
</style>
