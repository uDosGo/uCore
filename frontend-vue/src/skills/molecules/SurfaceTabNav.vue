<template>
  <nav
    class="surface-tab-nav"
    :class="[
      `surface-tab-nav--${orientation}`,
      { 'surface-tab-nav--has-toggle': showToggle }
    ]"
  >
    <!-- Orientation toggle icon -->
    <button
      v-if="showToggle"
      class="surface-tab-nav__toggle"
      :title="orientation === 'horizontal' ? 'Switch to vertical layout' : 'Switch to horizontal layout'"
      @click="toggleOrientation"
    >
      <UIcon :name="orientation === 'horizontal' ? 'swap_vert' : 'swap_horiz'" />
    </button>

    <!-- Tab links -->
    <a
      v-for="tab in tabs"
      :key="tab.id"
      class="surface-tab-nav__link"
      :class="{ 'surface-tab-nav__link--active': modelValue === tab.id }"
      href="#"
      @click.prevent="onTabClick(tab.id)"
    >
      <UIcon :name="tab.icon" class="surface-tab-nav__icon" />
      <span class="surface-tab-nav__label">{{ tab.label }}</span>
    </a>
  </nav>
</template>

<script setup lang="ts">
/**
 * @component SurfaceTabNav
 * @description Reusable tab navigation bar for surfaces. Supports horizontal (default)
 * and vertical orientations. Links are styled as nav links (not buttons) with underline
 * active state matching the GlobalToolbar tab style. Position can be toggled via an
 * inline icon button.
 *
 * @category molecules
 * @props {TabDef[]} tabs - Array of tab definitions with id, label, icon
 * @props {string} modelValue - Currently active tab id (v-model)
 * @props {'horizontal' | 'vertical'} orientation - Layout orientation
 * @props {boolean} showToggle - Whether to show the orientation toggle icon
 * @emits {'update:modelValue'} - Emitted when a tab is clicked
 * @emits {'toggle-orientation'} - Emitted when the orientation toggle is clicked
 * @usage
 *   <SurfaceTabNav
 *     v-model="activeTab"
 *     :tabs="MY_TABS"
 *     :orientation="shell.tabOrientation"
 *     @toggle-orientation="shell.toggleTabOrientation()"
 *   />
 */
import UIcon from '../atoms/UIcon.vue'

export interface TabDef {
  id: string
  label: string
  icon: string
}

interface Props {
  tabs: TabDef[]
  modelValue: string
  orientation?: 'horizontal' | 'vertical'
  showToggle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  orientation: 'horizontal',
  showToggle: false,
})

const emit = defineEmits<{
  'update:modelValue': [id: string]
  'toggle-orientation': []
}>()

function onTabClick(id: string) {
  emit('update:modelValue', id)
}

function toggleOrientation() {
  emit('toggle-orientation')
}
</script>

<style scoped>
/* ─── Base ─────────────────────────────────────────────────────────── */
.surface-tab-nav {
  display: flex;
  align-items: center;
  gap: 0;
  flex-shrink: 0;
  background: var(--usx-color-surface);
  overflow: hidden;
  box-sizing: border-box;
}

/* ─── Horizontal (default) ─────────────────────────────────────────── */
.surface-tab-nav--horizontal {
  flex-direction: row;
  justify-content: flex-start;
  padding: var(--usx-surface-tab-bar-padding);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  overflow-x: auto;
}

/* ─── Vertical ──────────────────────────────────────────────────────── */
.surface-tab-nav--vertical {
  flex-direction: column;
  justify-content: flex-start;
  padding: var(--usx-spacing-xs) 0;
  border-right: var(--usx-border-width) solid var(--usx-color-border);
  min-width: var(--usx-sidebar-compact-width, 56px);
  overflow-y: auto;
  align-items: stretch;
}

/* ─── Links — styled as nav (not buttons) ──────────────────────────── */
.surface-tab-nav__link {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-tab-padding);
  border: none;
  border-bottom: var(--usx-tab-border-width) solid transparent;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-medium);
  white-space: nowrap;
  transition: color var(--usx-transition-base), border-color var(--usx-transition-base);
  text-decoration: none;
  font-family: var(--usx-font-family-sans);
  min-height: var(--usx-touch-min);
  margin-bottom: calc(var(--usx-border-overlap) * -1);
  line-height: 1;
  -webkit-appearance: none;
  appearance: none;
}

/* No button-style effects */
.surface-tab-nav__link:hover {
  color: var(--usx-color-primary);
  border-bottom-color: transparent;
  background: transparent;
  box-shadow: none;
  outline: none;
}

.surface-tab-nav__link:active,
.surface-tab-nav__link:focus {
  background: transparent;
  box-shadow: none;
  outline: none;
}

.surface-tab-nav__link--active {
  color: var(--usx-color-primary);
  border-bottom-color: var(--usx-color-primary);
}

/* ─── Vertical link variant ───────────────────────────────────────── */
.surface-tab-nav--vertical .surface-tab-nav__link {
  border-bottom: none;
  border-left: var(--usx-tab-border-width) solid transparent;
  margin-bottom: 0;
  padding: var(--usx-spacing-sm) calc(var(--usx-spacing-md) + 1.35em + var(--usx-spacing-sm)) var(--usx-spacing-sm) var(--usx-spacing-md);
  justify-content: flex-start;
}

.surface-tab-nav--vertical .surface-tab-nav__link:hover {
  border-left-color: transparent;
}

.surface-tab-nav--vertical .surface-tab-nav__link--active {
  border-bottom-color: transparent;
  border-left-color: var(--usx-color-primary);
}

/* ─── Toggle orientation button ────────────────────────────────────── */
.surface-tab-nav__toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-xs);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: 1.25em;
  line-height: 1;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  flex-shrink: 0;
  transition: color var(--usx-transition-fast);
  -webkit-appearance: none;
  appearance: none;
}

.surface-tab-nav__toggle:hover {
  color: var(--usx-color-on-surface);
  background: transparent;
  box-shadow: none;
  outline: none;
}

.surface-tab-nav--horizontal .surface-tab-nav__toggle {
  margin-right: var(--usx-spacing-sm);
}

.surface-tab-nav--vertical .surface-tab-nav__toggle {
  align-self: center;
  margin-bottom: var(--usx-spacing-xs);
}

/* ─── Icon sizing — USX token-based, matches GlobalToolbar ── */
.surface-tab-nav__icon {
  flex-shrink: 0;
  width: var(--usx-icon-size-2lg);
  height: var(--usx-icon-size-2lg);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  vertical-align: middle;
}


</style>
