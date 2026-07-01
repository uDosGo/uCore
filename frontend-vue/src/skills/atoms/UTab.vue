<template>
  <button
    class="u-tab"
    :class="{ 'u-tab--active': active }"
    :disabled="disabled"
    :title="$slots.default ? String($slots.default()[0].children) : ''"
    @click="emit('click', $event)"
  >
    <UIcon v-if="icon" :name="icon" class="u-tab__icon" />
    <span class="u-tab__label">
      <slot />
    </span>
  </button>
</template>

<script setup lang="ts">
/**
 * @component UTab
 * @description Tab component with Pico nav-style underline styling.
 * Icon size is inherited from parent font-size (1em) — no hardcoded px.
 * Icon-to-label gap uses --usx-icon-label-gap (0.5em, Material3 standard).
 * @category atoms
 * @props {boolean} active - Whether the tab is currently active
 * @props {boolean} disabled - Disables the tab
 * @props {string} icon - Optional icon name (Iconify or Material)
 * @emits {MouseEvent} click - Fires on tab click
 * @usage <UTab active icon="mdi:home">Dashboard</UTab>
 */
import UIcon from './UIcon.vue'

interface Props {
  active?: boolean
  disabled?: boolean
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  active: false,
  disabled: false,
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<style scoped>
.u-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-icon-label-gap, 0.5em);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: none;
  background: transparent;
  color: var(--pico-muted-color);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
  border-radius: 0;
  border-bottom: 2px solid transparent;
  transition: color 0.15s ease, border-color 0.15s ease;
  font-weight: 500;
  font-family: var(--usx-font-family);
  margin-bottom: -1px;
}

/* Hover: icon inverts to primary color, no underline */
.u-tab:hover:not(:disabled) {
  color: var(--pico-primary);
  border-bottom-color: transparent;
}

.u-tab:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Active: primary color underline (only active tab gets underline) */
.u-tab--active {
  color: var(--pico-primary);
  border-bottom-color: var(--pico-primary);
}

/* Icon inherits font-size from parent (14px via --usx-font-size-sm) */
.u-tab__icon {
  flex-shrink: 0;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.u-tab__label {
  display: flex;
  align-items: center;
}

/* Icon-only mode on narrow screens */
@media (max-width: 768px) {
  .u-tab {
    padding: var(--usx-spacing-sm);
    min-width: 44px;
    justify-content: center;
  }

  .u-tab__label {
    display: none;
  }

  .u-tab__icon {
    margin: 0;
  }
}

/* Medium screens - keep text but reduce padding */
@media (max-width: 1024px) and (min-width: 769px) {
  .u-tab {
    padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  }
}
</style>
