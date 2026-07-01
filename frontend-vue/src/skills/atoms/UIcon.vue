<template>
  <span
    class="u-icon"
    :class="[`u-icon--${name}`, { 'u-icon--spin': spin }]"
    :title="title"
    role="img"
    :aria-label="title || name"
  >
    <!-- Material Symbols: plain names like "home", "menu", "settings" -->
    <span
      v-if="isMaterial"
      class="material-symbols-outlined"
    >
      {{ materialName }}
    </span>
    <!-- Iconify: names with colon like "mdi:home", "fa:bell" -->
    <iconify-icon
      v-else-if="isIconify"
      :icon="name"
      inline
    />
    <!-- Fallback: show first letter of icon name -->
    <span v-else class="u-icon__fallback">{{ fallbackChar }}</span>
  </span>
</template>

<script setup lang="ts">
/**
 * @component UIcon
 * @description Icon component supporting Iconify (MDI) and Material Symbols Outlined.
 * Icon size is relative to parent font-size by default (1em), but can be overridden
 * with a numeric px value via the `size` prop.
 *
 * Material3 standard: icons should be 1em relative to adjacent text.
 * For standalone icons (no text), use explicit px sizes.
 *
 * ## Icon Naming
 * Material Symbols uses **snake_case** (e.g. "chevron_right"), NOT kebab-case ("chevron-right").
 * Non-standard names are mapped to valid Material Symbols via MATERIAL_ICON_MAP.
 * See: https://fonts.google.com/icons
 *
 * @category atoms
 * @props {string} name - Icon name (Iconify format: "mdi:home" or Material: "home")
 * @props {number|string} size - Icon size in px (default: 1em, relative to font-size)
 * @props {boolean} spin - Whether to spin the icon
 * @props {string} title - Accessible title
 * @usage <UIcon name="mdi:home" :size="20" />
 * @usage <UIcon name="home" /> (Material Symbol, inherits font-size)
 */
import { computed } from 'vue'

interface Props {
  name: string
  size?: number | string
  spin?: boolean
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 0, // 0 means "use 1em" (relative to parent font-size)
  spin: false,
  title: '',
})

/**
 * Material Symbols Outlined — Name Mapping
 *
 * Maps common/custom names to valid Material Symbols Outlined codepoints.
 * Non-mapped names are passed through with kebab→snake normalization.
 *
 * Source: https://fonts.google.com/icons
 */
const MATERIAL_ICON_MAP: Record<string, string> = {
  // Kebab-case to snake_case conversions
  'chevron-right': 'chevron_right',
  // Original snake_case (already correct)
  'chevron_right': 'chevron_right',
  // Custom app names → valid Material Symbols
  'grid': 'grid_view',
  'server': 'dns',
  'flag': 'flag',
  'wrench': 'build',
  'key': 'key',
  'person': 'person',
  'school': 'school',
  'menu_book': 'menu_book',
  'storage': 'storage',
  'bookmark': 'bookmark',
  'build': 'build',
  'content_paste': 'content_paste',
  'psychology': 'psychology',
  'migration': 'import_export',
  'palette': 'palette',
  'backup': 'backup',
  'engineering': 'engineering',
  'play_arrow': 'play_arrow',
  'route': 'route',
  'dynamic_feed': 'dynamic_feed',
  'workflow': 'account_tree',
  'snack': 'restaurant_menu',
  'globe': 'public',
  'bolt': 'bolt',
  'tv': 'tv',
  'terminal': 'terminal',
  'help': 'help',
  'home': 'home',
  'settings': 'settings',
  'code': 'code',
  'menu': 'menu',
  'more_vert': 'more_vert',
  'search': 'search',
  'dashboard': 'dashboard',
  'folder': 'folder',
  'task': 'task',
  'article': 'article',
  'publish': 'publish',
  'edit_note': 'edit_note',
  'add': 'add',
  'visibility': 'visibility',
  'format_list_bulleted': 'format_list_bulleted',
  'smart_toy': 'smart_toy',
  'group': 'group',
  'attach_money': 'attach_money',
  'auto_stories': 'auto_stories',
  'food_croissant': 'food_croissant',
  'sync_alt': 'sync_alt',
  'sync': 'sync',
  'tune': 'tune',
  'schedule': 'schedule',
  'view_kanban': 'view_kanban',
  'extension': 'extension',
  'account_tree': 'account_tree',
  'chat': 'chat',
  'dns': 'dns',
  'restaurant_menu': 'restaurant_menu',
  'public': 'public',
  'grid_view': 'grid_view',
  'edit': 'edit',
  'save': 'save',
  'close': 'close',
  'view_column': 'view_column',
  'view_day': 'view_day',
}

/**
 * Normalize an icon name to a valid Material Symbols codepoint.
 * First checks the explicit map, then converts kebab-case to snake_case.
 */
function normalizeMaterialName(name: string): string {
  // Strip known prefixes
  const stripped = name
    .replace(/^material-symbols:/, '')
    .replace(/^material-icons:/, '')
  // Check explicit map first
  if (MATERIAL_ICON_MAP[stripped]) {
    return MATERIAL_ICON_MAP[stripped]
  }
  // Fallback: convert kebab-case to snake_case
  return stripped.replace(/-/g, '_')
}

/**
 * Detect if the icon name uses Iconify format (contains a colon, e.g. "mdi:home")
 * or is a plain Material Symbol name (e.g. "home", "settings", "search")
 */
const isIconify = computed(() => props.name.includes(':'))
const isMaterial = computed(() => !props.name.includes(':'))

/**
 * Extract and normalize the Material icon name.
 * Converts kebab-case → snake_case, maps custom names via MATERIAL_ICON_MAP.
 */
const materialName = computed(() => {
  return normalizeMaterialName(props.name)
})

/**
 * Fallback character: show first letter of icon name
 */
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
  /* Default: inherit font-size from parent (1em) */
  font-size: 1em;
  width: 1em;
  height: 1em;
}

/* Iconify icons render as inline SVG */
.u-icon :deep(iconify-icon) {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* Material Symbols — font-size inherited from .u-icon wrapper */
.u-icon .material-symbols-outlined {
  font-size: inherit;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Fallback */
.u-icon__fallback {
  font-size: 0.75em;
  opacity: 0.5;
}

/* Spin animation */
.u-icon--spin {
  animation: u-icon-spin 1s linear infinite;
}

@keyframes u-icon-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
