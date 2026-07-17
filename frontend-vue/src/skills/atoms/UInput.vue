<template>
  <div class="u-input" :class="{ 'u-input--disabled': disabled }">
    <UIcon v-if="icon" :name="icon" class="u-input__icon" />
    <input
      class="u-input__field"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :value="modelValue"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @keyup.enter="emit('enter', $event)"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * @component UInput
 * @description Text input with optional icon and disabled state.
 * @category atoms
 * @props {string} modelValue - v-model value
 * @props {string} type - Input type (text, password, etc.)
 * @props {string} placeholder - Placeholder text
 * @props {boolean} disabled - Disables the input
 * @props {string} icon - Optional icon name (Iconify)
 * @emits {string} update:modelValue - v-model update
 * @emits {KeyboardEvent} enter - Enter key pressed
 * @usage <UInput v-model="query" placeholder="Search..." icon="search" />
 */
import UIcon from './UIcon.vue'

interface Props {
  modelValue?: string
  type?: string
  placeholder?: string
  disabled?: boolean
  icon?: string
}

withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  placeholder: '',
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  enter: [event: KeyboardEvent]
}>()
</script>

<style scoped>
.u-input {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  border-radius: var(--usx-radius-md);
  padding: 0 var(--usx-spacing-lg);
  background: var(--usx-color-surface-variant);
  transition: background var(--usx-transition-fast);
  height: var(--usx-touch-min);
  min-height: var(--usx-touch-min);
  border: var(--usx-border-width) solid var(--usx-color-border);
  box-sizing: border-box;
}

.u-input:focus-within {
  border-color: var(--usx-color-primary);
  background: var(--usx-color-surface);
}

.u-input__icon {
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15em;
}

.u-input__field {
  border: none;
  background: transparent;
  outline: none;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
  width: 100%;
  height: 100%;
  font-family: var(--usx-font-family-sans);
  padding: 0;
  line-height: var(--usx-line-height-normal);
  margin: 0;
  -webkit-appearance: none;
  appearance: none;
}

.u-input__field:focus {
  outline: none;
  box-shadow: none;
}

.u-input__field::placeholder {
  color: var(--usx-color-on-surface-muted);
  opacity: 0.7;
}

.u-input--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
