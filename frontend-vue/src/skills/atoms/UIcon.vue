<template>
  <span
    class="u-icon"
    :class="[`u-icon--${name}`, { 'u-icon--spin': spin }]"
    :title="title"
    role="img"
    :aria-label="title || name"
  >
    <svg
      v-if="svgIcon"
      class="u-icon__svg"
      viewBox="0 0 24 24"
      aria-hidden="true"
      v-html="svgIcon"
    />
    <!-- Material Symbols: plain names like "home", "menu", "settings" -->
    <span
      v-else-if="isMaterial"
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
  // Status & action icons
  'add_circle': 'add_circle',
  'check_circle': 'check_circle',
  'delete': 'delete',
  'circle': 'circle',
  'description': 'description',
  'error': 'error',
  'warning': 'warning',
  'mail': 'mail',
  'push_pin': 'push_pin',
  'cable': 'cable',
  'my_location': 'my_location',
  'download': 'download',
  'bar_chart': 'bar_chart',
  'rss_feed': 'rss_feed',
  'inventory': 'inventory',
  'restart_alt': 'restart_alt',
  'import_export': 'import_export',
  'input': 'input',
  'progress_activity': 'progress_activity',
}

const MATERIAL_SVG_ICONS: Record<string, string> = {
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  swap_vert: '<path d="M8 4v14m0 0-3-3m3 3 3-3M16 20V6m0 0-3 3m3-3 3 3"/>',
  swap_horiz: '<path d="M4 8h14m0 0-3-3m3 3-3 3M20 16H6m0 0 3-3m-3 3 3 3"/>',
  home: '<path d="M4 11.5 12 5l8 6.5"/><path d="M6.5 10.5V20h11v-9.5"/><path d="M10 20v-5h4v5"/>',
  visibility: '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="3"/>',
  lightbulb: '<path d="M9 18h6"/><path d="M10 21h4"/><path d="M8 10a4 4 0 1 1 8 0c0 2-1.2 3-2.1 4.1-.5.6-.8 1.2-.9 1.9h-2c-.1-.7-.4-1.3-.9-1.9C9.2 13 8 12 8 10Z"/>',
  light_mode: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M2 12h2.5M19.5 12H22M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M4.7 4.7l2.1 2.1M17.2 17.2l2.1 2.1M2.5 12h3M18.5 12h3M4.7 19.3l2.1-2.1M17.2 6.8l2.1-2.1"/>',
  terminal: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m7 9 3 3-3 3M12 15h5"/>',
  tv: '<rect x="4" y="7" width="16" height="11" rx="2"/><path d="m9 4 3 3 3-3"/>',
  grid_on: '<path d="M4 4h16v16H4zM4 9.3h16M4 14.7h16M9.3 4v16M14.7 4v16"/>',
  grid_view: '<path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/>',
  dashboard: '<path d="M4 4h7v7H4zM13 4h7v5h-7zM13 11h7v9h-7zM4 13h7v7H4z"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m4 12 8 4.5 8-4.5M4 16l8 4.5 8-4.5"/>',
  refresh: '<path d="M20 6v5h-5"/><path d="M19 11a7 7 0 1 0-2.1 5"/>',
  save: '<path d="M5 4h12l2 2v14H5z"/><path d="M8 4v6h8V4M8 20v-6h8v6"/>',
  folder_open: '<path d="M3 7h7l2 2h9v3"/><path d="M3 10h18l-2 9H5z"/>',
  folder: '<path d="M3 6h7l2 2h9v11H3z"/>',
  palette: '<path d="M12 4a8 8 0 0 0 0 16h1.5a2 2 0 0 0 0-4H12a2 2 0 0 1 0-4h1a7 7 0 0 0 7-7c-1.8-1.9-4.6-3-8-3Z"/><circle cx="8" cy="10" r=".7"/><circle cx="11" cy="8" r=".7"/><circle cx="15" cy="9" r=".7"/>',
  edit: '<path d="M4 20h4l11-11-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
  format_paint: '<path d="M4 5h11v5H4z"/><path d="M15 7h3a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2h-5v3"/><path d="M11 15h4v5h-4z"/>',
  ink_eraser: '<path d="m4 16 8-8 6 6-6 6H7z"/><path d="m10 10 6 6M3 20h18"/>',
  colorize: '<path d="m14 4 6 6-8 8H6v-6z"/><path d="m12 6 6 6"/>',
  add: '<path d="M12 5v14M5 12h14"/>',
  add_circle: '<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  check_circle: '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',
  chevron_left: '<path d="m15 6-6 6 6 6"/>',
  chevron_right: '<path d="m9 6 6 6-6 6"/>',
  circle: '<circle cx="12" cy="12" r="8"/>',
  close: '<path d="m6 6 12 12M18 6 6 18"/>',
  delete: '<path d="M5 7h14M10 11v6M14 11v6M8 7l1-3h6l1 3M7 7l1 13h8l1-13"/>',
  download: '<path d="M12 4v10m0 0 4-4m-4 4-4-4"/><path d="M5 20h14"/>',
  error: '<circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/>',
  expand_more: '<path d="m6 9 6 6 6-6"/>',
  file_download: '<path d="M6 20h12"/><path d="M12 4v10m0 0 4-4m-4 4-4-4"/>',
  preview: '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="3"/>',
  send: '<path d="M4 20 20 12 4 4l3 8-3 8Z"/><path d="M7 12h13"/>',
  remove: '<path d="M5 12h14"/>',
  rss_feed: '<path d="M5 5a14 14 0 0 1 14 14"/><path d="M5 11a8 8 0 0 1 8 8"/><circle cx="6" cy="18" r="1.5"/>',
  inventory: '<path d="M4 7h16v13H4z"/><path d="M4 7l2-3h12l2 3M9 11h6"/>',
  description: '<path d="M6 3h9l3 3v15H6z"/><path d="M14 3v4h4M8 12h8M8 16h8"/>',
  sync: '<path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M18 12a6 6 0 0 0-10-4.5L4 12M6 12a6 6 0 0 0 10 4.5L20 12"/>',
  progress_activity: '<path d="M12 3a9 9 0 1 1-8.5 6"/>',
  search: '<circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5"/>',
  more_vert: '<circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/>',
  verified: '<path d="m9 12 2 2 4-5"/><path d="m12 3 2.2 1.7 2.8-.2 1 2.6 2.4 1.5-.9 2.7.9 2.7-2.4 1.5-1 2.6-2.8-.2L12 21l-2.2-1.7-2.8.2-1-2.6-2.4-1.5.9-2.7-.9-2.7L6 8.5l1-2.6 2.8.2L12 3Z"/>',
  warning: '<path d="M12 4 3 20h18L12 4Z"/><path d="M12 9v5M12 17h.01"/>',
  cloud_off: '<path d="m4 4 16 16"/><path d="M8.5 18H7a4 4 0 0 1-.7-7.9A6 6 0 0 1 17.4 8"/><path d="M18 18a3 3 0 0 0 1.2-5.8"/>',
  code: '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/>',
  monitor_heart: '<path d="M4 5h16v11H4z"/><path d="M8 20h8M12 16v4"/><path d="M7 11h2l1-2 2 5 1.5-3H17"/>',
  build: '<path d="m14.7 6.3 3-3a5 5 0 0 1-6.4 6.4l-6.5 6.5a2 2 0 0 0 2.8 2.8l6.5-6.5a5 5 0 0 1 .6-6.2Z"/>',
  bar_chart: '<path d="M5 19V9M12 19V5M19 19v-7"/>',
  view_kanban: '<path d="M4 5h16v14H4z"/><path d="M9 5v14M15 5v14"/>',
  cable: '<path d="M7 7h5v5H7zM12 9h4a3 3 0 0 1 0 6h-4M7 17h5v-5H7z"/>',
  extension: '<path d="M8 4h4v4h4v4h4v4h-4v4h-4v-4H8v-4H4V8h4z"/>',
  my_location: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/><circle cx="12" cy="12" r="8"/>',
  dns: '<rect x="4" y="5" width="16" height="5" rx="1"/><rect x="4" y="14" width="16" height="5" rx="1"/><path d="M7 7.5h.01M7 16.5h.01"/>',
  smart_toy: '<rect x="5" y="8" width="14" height="10" rx="3"/><path d="M12 4v4M9 4h6M9 14h6"/><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/>',
  group: '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="10" r="2.5"/><path d="M3 20a6 6 0 0 1 12 0M14 20a5 5 0 0 1 7 0"/>',
  bolt: '<path d="M13 2 4 14h7l-1 8 10-13h-7z"/>',
  flag: '<path d="M5 21V4h11l1 4-1 4H5"/>',
  restaurant_menu: '<path d="M7 3v8M4 3v4a3 3 0 0 0 6 0V3M7 11v10M17 3v18M14 3v8a3 3 0 0 0 3 3"/>',
  public: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 2-2.5 2-2.5 4M12 17h.01"/>',
  music_note: '<path d="M9 18a3 3 0 1 1-2-2.8V5l11-2v11a3 3 0 1 1-2-2.8V7L9 8z"/>',
  usb: '<path d="M12 3v12M8 7l4-4 4 4M6 13h4M6 13a2 2 0 1 0 0 4h4M18 13h-4M18 13a2 2 0 1 1 0 4h-4M12 15v6"/>',
  workflow: '<path d="M6 6h4v4H6zM14 14h4v4h-4zM6 18h4v-4H6zM10 8h4v8h-4"/>',
  account_tree: '<path d="M6 4h5v5H6zM14 15h5v5h-5zM4 15h5v5H4zM8.5 9v3h8v3M8.5 12H6.5v3"/>',
  school: '<path d="m12 4 10 5-10 5L2 9l10-5Z"/><path d="M6 11v5c3 2 9 2 12 0v-5"/>',
  menu_book: '<path d="M4 5h6a3 3 0 0 1 3 3v12a3 3 0 0 0-3-3H4zM20 5h-6a3 3 0 0 0-3 3v12a3 3 0 0 1 3-3h6z"/>',
  storage: '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/>',
  sync_alt: '<path d="M4 8h14m0 0-3-3m3 3-3 3M20 16H6m0 0 3-3m-3 3 3 3"/>',
  schedule: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  publish: '<path d="M12 16V4m0 0-4 4m4-4 4 4"/><path d="M5 20h14"/>',
  task: '<path d="M6 4h12v16H6z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
  archive: '<path d="M4 6h16v4H4z"/><path d="M6 10v10h12V10M10 14h4"/>',
  open_in_new: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M10 6H5v13h13v-5"/>',
  article: '<path d="M6 3h9l3 3v15H6z"/><path d="M14 3v4h4M8 11h8M8 15h8M8 18h5"/>',
  content_paste: '<path d="M9 4h6v3H9z"/><path d="M8 5H6v16h12V5h-2"/>',
  key: '<circle cx="8" cy="14" r="4"/><path d="M12 14h8M17 14v3M20 14v3"/>',
  person: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  tune: '<path d="M4 7h10M18 7h2M4 17h2M10 17h10M12 5v4M8 15v4"/>',
  alt_route: '<path d="M6 3v4a4 4 0 0 0 4 4h4M18 3v18M15 18l3 3 3-3M15 6l3-3 3 3"/>',
  memory: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
  tips_and_updates: '<path d="M9 18h6M10 21h4"/><path d="M8 10a4 4 0 1 1 8 0c0 2-1.2 3-2.1 4.1-.5.6-.8 1.2-.9 1.9h-2c-.1-.7-.4-1.3-.9-1.9C9.2 13 8 12 8 10Z"/><path d="M3 10h2M19 10h2M5 4l1.5 1.5M17.5 5.5 19 4"/>',
  rocket_launch: '<path d="M5 19c2-5 6-11 14-14-3 8-9 12-14 14Z"/><path d="M9 15 5 19l4-1M9 15l-3-3M14 6l4 4"/><circle cx="15" cy="9" r="1.5"/>',
  widgets: '<path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/>',
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

const svgIcon = computed(() => {
  return isMaterial.value ? MATERIAL_SVG_ICONS[materialName.value] || '' : ''
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
  font-size: 1em;
}

/* Iconify icons render as inline SVG */
.u-icon :deep(iconify-icon) {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.u-icon__svg {
  width: 1em;
  height: 1em;
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  overflow: visible;
}

/* Material Symbols — Material 3 compliant */
.u-icon .material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  user-select: none;
  font-display: swap;
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
