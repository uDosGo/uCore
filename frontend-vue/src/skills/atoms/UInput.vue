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
  justify-content: center;
  gap: var(--usx-spacing-xs);
  border-radius: var(--usx-border-radius-md);
  padding: var(--usx-button-padding-vertical) var(--usx-button-padding-horizontal);
  background: var(--pico-background-color);
  transition: background 0.15s ease;
  height: var(--usx-input-height, 40px);
  min-height: var(--usx-input-height, 40px);
}

.u-input:focus-within {
  background: #1a2332;
}

.u-input__icon {
  color: var(--pico-muted-color);
  flex-shrink: 0;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.u-input__field {
  border: none;
  background: transparent;
  outline: none;
  font-size: var(--usx-font-size-base);
  color: var(--pico-color);
  width: 100%;
}

.u-input--disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--pico-background-color);
}
</style>
