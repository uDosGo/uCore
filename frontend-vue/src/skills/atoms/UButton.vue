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
  if (props.size === 'sm') return 14
  if (props.size === 'lg') return 20
  return 16
})

import { computed } from 'vue'
</script>

<style scoped>
.u-button {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  border-radius: var(--usx-border-radius-md);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.15s ease;
  font-family: var(--usx-font-family);
}

.u-button--sm { padding: var(--usx-spacing-sm) var(--usx-spacing-md); font-size: var(--usx-font-size-sm); }
.u-button--md { padding: var(--usx-button-padding-vertical) var(--usx-button-padding-horizontal); font-size: var(--usx-font-size-base); }
.u-button--lg { padding: var(--usx-spacing-lg) var(--usx-spacing-xl); font-size: var(--usx-font-size-lg); }

.u-button--primary {
  background: var(--pico-primary);
  color: #fff;
}
.u-button--primary:hover { background: var(--pico-primary-hover); }

.u-button--secondary {
  background: var(--pico-background-color);
  color: var(--pico-color);
}
.u-button--secondary:hover { background: #1a2332; }

.u-button--ghost {
  background: transparent;
  color: var(--pico-color);
}
.u-button--ghost:hover { background: #1a2332; opacity: 0.7; }

.u-button--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.u-button__icon {
  flex-shrink: 0;
}
</style>
