<template>
  <span
    class="u-icon"
    :class="[{ 'u-icon--spin': spin }]"
    :title="title"
    role="img"
    :aria-label="title || name"
  >
    <!-- Material Symbols: self-hosted font, offline-first, ligature rendering -->
    <span
      v-if="isMaterial"
      class="material-symbols-outlined u-icon__glyph"
    >{{ materialName }}</span>
    <!-- Iconify: colon-prefixed names like "mdi:home" -->
    <iconify-icon
      v-else-if="isIconify"
      :icon="name"
      inline
    />
    <!-- Fallback -->
    <span v-else class="u-icon__fallback">{{ fallbackChar }}</span>
  </span>
</template>

<script setup lang="ts">
/**
 * @component UIcon
 * @description Offline-first icon component using self-hosted Material Symbols font
 * (npm package: material-symbols) with zero network dependency at runtime.
 * Iconify icons (colon-prefixed names like "mdi:home") use the CDN-loaded web component.
 *
 * ## Icon Naming
 * Uses snake_case Material Symbols names (e.g. "settings", "dark_mode").
 * Kebab-case names (e.g. "chevron-right") are auto-converted to snake_case.
 * Legacy short names (e.g. "grid", "server", "snack", "globe") are mapped
 * to their canonical Material Symbols names.
 *
 * @category atoms
 * @props {string} name - Icon name
 * @props {boolean} spin - Whether to spin the icon
 * @props {string} title - Accessible title
 */
import { computed } from 'vue'

interface Props {
  name: string
  spin?: boolean
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  spin: false,
  title: '',
})

const isIconify = computed(() => props.name.includes(':'))
const isMaterial = computed(() => !props.name.includes(':'))

/**
 * Short-name aliases used by data objects in stores and the router.
 * Maps legacy/custom names to canonical Material Symbols ligature names.
 */
const ALIAS_MAP: Record<string, string> = {
  'grid': 'grid_view',
  'server': 'dns',
  'snack': 'restaurant_menu',
  'globe': 'public',
  'wrench': 'build',
  'migration': 'import_export',
  'workflow': 'account_tree',
}

function resolveAlias(name: string): string {
  return ALIAS_MAP[name] || name
}

function toSnakeCase(name: string): string {
  return name.replace(/-/g, '_')
}

const materialName = computed(() => {
  if (isIconify.value) return ''
  const stripped = props.name
    .replace(/^material-symbols:/, '')
    .replace(/^material-icons:/, '')
  const resolved = resolveAlias(stripped)
  return toSnakeCase(resolved)
})

const fallbackChar = computed(() => {
  return props.name.charAt(0).toUpperCase() || '?'
})
</script>

<style scoped>
.u-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1;
  vertical-align: middle;
  font-size: 1em;
}

/* Material Symbols glyph — self-hosted woff2, uses ligatures */
.u-icon__glyph {
  font-size: 1em;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Iconify icons render as inline SVG */
.u-icon :deep(iconify-icon) {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* Fallback */
.u-icon__fallback {
  font-size: 0.75em;
  opacity: 0.5;
}

/* Spin animation */
.u-icon--spin {
  animation: u-icon-spin var(--usx-motion-duration-spin) linear infinite;
}

@keyframes u-icon-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>