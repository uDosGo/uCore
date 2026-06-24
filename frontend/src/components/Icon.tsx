import React from 'react'
import * as LucideIcons from 'lucide-react'

export interface IconProps {
  name: string
  /** Explicit size in px. Omit to inherit from CSS context (recommended). */
  size?: number
  className?: string
  style?: React.CSSProperties
}

/**
 * Material Symbol -> Lucide React icon name mapping.
 * Maps canonical Material Design icon names to Lucide equivalents.
 */
const LUCIDE_MAP: Record<string, keyof typeof LucideIcons> = {
  add: 'Plus',
  check_circle: 'CheckCircle2',
  sync: 'RotateCw',
  hourglass_empty: 'Hourglass',
  radio_button_unchecked: 'Circle',
  stop_circle: 'StopCircle',
  error: 'AlertCircle',
  grid_view: 'Grid3x3',
  widgets: 'Layout',
  smart_toy: 'Bot',
  menu_book: 'BookOpen',
  build: 'Wrench',
  tune: 'Sliders',
  play_circle: 'PlayCircle',
  play_arrow: 'Play',
  visibility: 'Eye',
  refresh: 'RotateCcw',
  bug_report: 'Bug',
  delete: 'Trash2',
  analytics: 'BarChart3',
  star: 'Star',
  checklist: 'CheckSquare',
  history: 'History',
  chat: 'MessageSquare',
  bolt: 'Zap',
  apps: 'Grid',
  download: 'Download',
  language: 'Globe',
  auto_awesome: 'Sparkles',
  arrow_back: 'ArrowLeft',
  web: 'Globe',
  terminal: 'Terminal',
  folder: 'Folder',
  map: 'Map',
  puzzle: 'Puzzle',
  account_tree: 'GitBranch',
  settings_suggest: 'Settings',
  school: 'BookMarked',
  code: 'Code',
  commit: 'GitCommit',
  open_in_new: 'ExternalLink',
  chevron_up: 'ChevronUp',
  chevron_down: 'ChevronDown',
  unfold_less: 'ChevronsUp',
  unfold_more: 'ChevronsDown',
  view_in_ar: 'Box',
  palette: 'Palette',
  link: 'Link',
  query_stats: 'BarChart4',
  monitor_heart: 'Heart',
  restaurant_menu: 'Menu',
  layers: 'Layers',
  close: 'X',
  auto_stories: 'BookOpen',
  debug: 'Bug',
  dashboard: 'LayoutDashboard',
  /* --- GlobalToolbar --- */
  home: 'Home',
  settings: 'Settings',
  flag: 'Flag',
  /* --- Workflow Surface --- */
  description: 'FileText',
  edit: 'Edit2',
  folder_open: 'FolderOpen',
  folder_special: 'FolderCheck',
  info: 'Info',
  input: 'ArrowRight',
  list: 'List',
  priority_high: 'AlertTriangle',
  search: 'Search',
  help: 'HelpCircle',
  cloud_upload: 'CloudUpload',
  upload_file: 'Upload',
  publish: 'Send',
  rocket_launch: 'Rocket',
  fact_check: 'CheckCircle2',
  component_exchange: 'ArrowRightLeft',
  folder_sync: 'RefreshCw',
  /* --- Misc UI --- */
  check: 'Check',
  more_vert: 'MoreVertical',
  arrow_forward: 'ArrowRight',
  arrow_upward: 'ArrowUp',
  arrow_downward: 'ArrowDown',
  warning: 'AlertTriangle',
  info_outline: 'Info',
  help_outline: 'HelpCircle',
  done_all: 'CheckCheck',
  cancel: 'XCircle',
  redo: 'Redo2',
  undo: 'Undo2',
  dns: 'Server',
}

export const Icon: React.FC<IconProps> = ({ name, size = 24, className, style }) => {
  const lucideName = LUCIDE_MAP[name] || name
  const IconComponent = (LucideIcons as any)[lucideName]

  if (!IconComponent) {
    console.warn(`Icon not found: ${name} (resolved to: ${lucideName})`)
    return <span className={className} style={style} aria-hidden="true" />
  }

  const inlineStyle: React.CSSProperties = {
    width: size,
    height: size,
    ...style,
  }

  return (
    <IconComponent
      size={size}
      className={className}
      style={inlineStyle}
      aria-hidden="true"
    />
  )
}

export default Icon
