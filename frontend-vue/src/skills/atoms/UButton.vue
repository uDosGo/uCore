<template>
  <button
    class="u-button"
    :class="[`u-button--${variant}`, `u-button--${size}`, { 'u-button--disabled': disabled }]"
    :disabled="disabled"
    @click="emit('click', $event)"
  >
    <UIcon v-if="icon" :name="icon" :size="iconSize" class="u-button__icon" />
    <span class="u-button__label">
      <slot />
    </span>
  </button>
</template>

<script setup lang="ts">
/**
 * @component UButton
 * @description Primary action button with variant, size, and icon support.
 * @category atoms
 * @props {'primary' | 'secondary' | 'ghost'} variant - Visual style variant
 * @props {'sm' | 'md' | 'lg'} size - Button size
 * @props {boolean} disabled - Disables the button
 * @props {string} icon - Optional icon name (Iconify)
 * @emits {MouseEvent} click - Fires on button click
 * @usage <UButton variant="primary" size="md" icon="check">Submit</UButton>
 */
import UIcon from './UIcon.vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const iconSize = computed(() => {
  if (props.size === 'sm') return 16
  if (props.size === 'lg') return 24
  return 20
})

import { computed } from 'vue'
</script>

<style scoped>
.u-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  font-weight: var(--usx-font-weight-medium);
  line-height: var(--usx-line-height-tight);
  transition: all 0.15s ease;
  font-family: var(--usx-font-family-sans);
  border: var(--usx-border-width) solid transparent;
}

.u-button--sm { padding: var(--usx-spacing-sm) var(--usx-spacing-lg); font-size: var(--usx-font-size-sm); }
.u-button--md { padding: var(--usx-spacing-md) var(--usx-spacing-xl); font-size: var(--usx-font-size-base); }
.u-button--lg { padding: var(--usx-spacing-lg) calc(var(--usx-spacing-xl) + var(--usx-spacing-sm)); font-size: var(--usx-font-size-lg); }

.u-button--primary {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}
.u-button--primary:hover { background: var(--usx-color-primary-hover); }

.u-button--secondary {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
  border-color: var(--usx-color-border);
}
.u-button--secondary:hover { background: var(--usx-color-surface-hover); }

.u-button--ghost {
  background: transparent;
  color: var(--usx-color-on-surface-muted);
}
.u-button--ghost:hover { color: var(--usx-color-on-surface); background: var(--usx-color-surface-hover); }

.u-button--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.u-button__icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  line-height: 1;
}

.u-button__label {
  line-height: var(--usx-line-height-tight);
}
</style>
