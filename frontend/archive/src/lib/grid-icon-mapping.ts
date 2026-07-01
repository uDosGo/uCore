// GridCore Icon Mapping
// Maps USX concepts to Google Material 3 Icons
// Usage: import { gridIconMap } from '@/lib/grid-icon-mapping';

export const gridIconMap = {
  // Core grid operations
  grid: 'grid_view',
  cell: 'crop_square',
  row: 'view_column',
  column: 'view_column',
  focus: 'center_focus_strong',
  selection: 'select_all',

  // Media operations
  play: 'play_arrow',
  pause: 'pause',
  stop: 'stop',
  record: 'fiber_manual_record',
  rewind: 'fast_rewind',
  forward: 'fast_forward',
  volume: 'volume_up',
  volumeOff: 'volume_off',

  // Navigation
  home: 'home',
  browse: 'browse_gallery',
  search: 'search',
  settings: 'settings',
  user: 'person',
  logout: 'logout',
  menu: 'menu',
  close: 'close',
  arrowBack: 'arrow_back',
  arrowForward: 'arrow_forward',
  chevronLeft: 'chevron_left',
  chevronRight: 'chevron_right',

  // Automation
  automation: 'smart_toy',
  device: 'devices',
  scene: 'scene',
  trigger: 'bolt',
  schedule: 'schedule',

  // File/Content
  folder: 'folder',
  file: 'insert_drive_file',
  image: 'image',
  video: 'video_library',
  music: 'music_note',
  document: 'description',

  // Status
  online: 'wifi',
  offline: 'wifi_off',
  warning: 'warning',
  error: 'error',
  success: 'check_circle',
  pending: 'pending',
  info: 'info',
  help: 'help',

  // UI Elements
  add: 'add',
  remove: 'remove',
  edit: 'edit',
  delete: 'delete',
  save: 'save',
  copy: 'copy',
  paste: 'paste',
  download: 'download',
  upload: 'upload',
  refresh: 'refresh',
  share: 'share',
  moreVert: 'more_vert',
  star: 'star',
  favorite: 'favorite',
  starBorder: 'star_border',

  // GridSmith specific
  gridSmith: 'grid_on',
  uCode: 'code',
  surface: 'surround_sound',
  template: 'template',
  export: 'export',
  import: 'import_export',
  build: 'build',
  debug: 'bug_report',
  test: 'test',
  deploy: 'cloud_upload',
  version: 'version',
} as const;

// Reverse mapping (icon name to concept)
export const iconToConceptMap: Record<string, string> = Object.fromEntries(
  Object.entries(gridIconMap).map(([concept, icon]) => [icon, concept])
);

// Get icon by concept
export const getIcon = (concept: string): string => {
  return gridIconMap[concept as keyof typeof gridIconMap] || 'help';
};

// Get concept by icon name
export const getConcept = (iconName: string): string => {
  return iconToConceptMap[iconName] || 'help';
};