// Icon Component
// Abstracted icon system using Google Material 3 Icons
// Usage: <Icon name="home" size="md" />

import React from 'react';
import * as MaterialIcons from '@mui/icons-material';

// Icon size mapping (px)
const sizeMap = {
  sm: 18,
  md: 24,
  lg: 36,
  xl: 48,
};

// Icon name mapping to Material Icons
const iconMap: Record<string, React.ComponentType<any>> = {
  // Core grid operations
  grid: MaterialIcons.GridView,
  grid_view: MaterialIcons.GridView, // Added for dashboard
  cell: MaterialIcons.CropSquare,
  row: MaterialIcons.ViewColumn,
  column: MaterialIcons.ViewColumn,
  focus: MaterialIcons.CenterFocusStrong,
  selection: MaterialIcons.SelectAll,

  // Media operations
  play: MaterialIcons.PlayArrow,
  pause: MaterialIcons.Pause,
  stop: MaterialIcons.Stop,
  record: MaterialIcons.FiberManualRecord,
  rewind: MaterialIcons.FastRewind,
  forward: MaterialIcons.FastForward,
  volume: MaterialIcons.VolumeUp,
  volumeOff: MaterialIcons.VolumeOff,

  // Navigation
  home: MaterialIcons.Home,
  browse: MaterialIcons.BrowseGallery,
  search: MaterialIcons.Search,
  settings: MaterialIcons.Settings,
  user: MaterialIcons.Person,
  logout: MaterialIcons.Logout,
  menu: MaterialIcons.Menu,
  close: MaterialIcons.Close,
  arrowBack: MaterialIcons.ArrowBack,
  arrowForward: MaterialIcons.ArrowForward,
  chevronLeft: MaterialIcons.ChevronLeft,
  chevronRight: MaterialIcons.ChevronRight,

  // Automation
  automation: MaterialIcons.SmartToy,
  device: MaterialIcons.Devices,
  scene: MaterialIcons.Landscape, // Alternative: Scene not available
  trigger: MaterialIcons.Bolt,
  schedule: MaterialIcons.Schedule,

  // File/Content
  folder: MaterialIcons.Folder,
  file: MaterialIcons.InsertDriveFile,
  image: MaterialIcons.Image,
  video: MaterialIcons.VideoLibrary,
  music: MaterialIcons.MusicNote,
  document: MaterialIcons.Description,

  // Status
  online: MaterialIcons.Wifi,
  offline: MaterialIcons.WifiOff,
  warning: MaterialIcons.Warning,
  error: MaterialIcons.Error,
  success: MaterialIcons.CheckCircle,
  pending: MaterialIcons.Pending,
  info: MaterialIcons.Info,
  help: MaterialIcons.Help,

  // UI Elements
  add: MaterialIcons.Add,
  remove: MaterialIcons.Remove,
  edit: MaterialIcons.Edit,
  delete: MaterialIcons.Delete,
  save: MaterialIcons.Save,
  copy: MaterialIcons.ContentCopy, // Fixed: Copy -> ContentCopy
  paste: MaterialIcons.ContentPaste, // Fixed: Paste -> ContentPaste
  download: MaterialIcons.Download,
  upload: MaterialIcons.Upload,
  refresh: MaterialIcons.Refresh,
  share: MaterialIcons.Share,
  moreVert: MaterialIcons.MoreVert,
  star: MaterialIcons.Star,
  favorite: MaterialIcons.Favorite,
  starBorder: MaterialIcons.StarBorder,
  
  // Snackbar Mac Tray Icons
  hamburger: MaterialIcons.Menu as React.ComponentType<any>, // 🍔 SnackShack
  fastfood: MaterialIcons.Fastfood as React.ComponentType<any>, // 🍟 SnackMachine
  sentimentVerySatisfied: MaterialIcons.SentimentVerySatisfied as React.ComponentType<any>, // 😊 Happy
  sentimentVeryDissatisfied: MaterialIcons.SentimentVeryDissatisfied as React.ComponentType<any>, // 😢 Sad
  clipboard: MaterialIcons.ContentPaste as React.ComponentType<any>, // 💥 Clipboard
  clipboardBoom: MaterialIcons.Delete as React.ComponentType<any>, // 💥 Boom effect

  // GridSmith specific
  gridSmith: MaterialIcons.GridOn,
  uCode: MaterialIcons.Code,
  surface: MaterialIcons.SurroundSound,
  template: MaterialIcons.Description, // Fixed: Template -> Description
  export: MaterialIcons.IosShare, // Fixed: Export -> IosShare
  import: MaterialIcons.ImportExport,
  build: MaterialIcons.Build,
  debug: MaterialIcons.BugReport,
  test: MaterialIcons.Science, // Fixed: TestTube -> Science
  deploy: MaterialIcons.CloudUpload,
  version: MaterialIcons.History, // Fixed: Version -> History

  // Additional icons
  tune: MaterialIcons.Tune,
  person: MaterialIcons.Person,
  map: MaterialIcons.Map,
  bolt: MaterialIcons.Bolt,
  dashboard: MaterialIcons.Dashboard,
  hub: MaterialIcons.Hub,
  sync: MaterialIcons.Sync,
  vertical_split: MaterialIcons.VerticalSplit,
  toggle_on: MaterialIcons.ToggleOn,
  keyboard: MaterialIcons.Keyboard,
  chat: MaterialIcons.Chat,
  dark_mode: MaterialIcons.DarkMode,
  light_mode: MaterialIcons.LightMode,
  brightness_auto: MaterialIcons.BrightnessAuto,
  dns: MaterialIcons.Dns,
  text_fields: MaterialIcons.TextFields,
  format_size: MaterialIcons.FormatSize,
  palette: MaterialIcons.Palette,
  computer: MaterialIcons.Computer,
  add_circle: MaterialIcons.AddCircle,
  key: MaterialIcons.Key,
  badge: MaterialIcons.Badge,
  location_on: MaterialIcons.LocationOn,
  fingerprint: MaterialIcons.Fingerprint,
  content_paste: MaterialIcons.ContentPaste,
  settings_suggest: MaterialIcons.SettingsSuggest,
  auto_stories: MaterialIcons.AutoStories,
  account_tree: MaterialIcons.AccountTree,
  compare_arrows: MaterialIcons.CompareArrows,
  monitor_heart: MaterialIcons.MonitorHeart,
  school: MaterialIcons.School,
  rocket_launch: MaterialIcons.RocketLaunch,
  folder_special: MaterialIcons.FolderSpecial,
  flag: MaterialIcons.Flag,
  checklist: MaterialIcons.Checklist,
  publish: MaterialIcons.Publish,
  restaurant_menu: MaterialIcons.RestaurantMenu,
  power: MaterialIcons.Power,
  history: MaterialIcons.History,
  network_check: MaterialIcons.NetworkCheck,
  lock: MaterialIcons.Lock,
  storage: MaterialIcons.Storage,
  system_update: MaterialIcons.SystemUpdate,
  terminal: MaterialIcons.Terminal,
  check_circle: MaterialIcons.CheckCircle,
  cloud_off: MaterialIcons.CloudOff,
  tv: MaterialIcons.Tv, // Added for Teletext
  draw: MaterialIcons.Draw, // Added for Grid Editor
  layers: MaterialIcons.Layers, // Added for Layer Composer
  font_download: MaterialIcons.FontDownload, // Added for SVG Font Mapper
  explore: MaterialIcons.Explore, // Added for Spatial Algebra
  smart_toy: MaterialIcons.SmartToy, // Added for GridSmith
  
  // Snackbar Mac Tray Icons (macOS)
  restaurant: MaterialIcons.Restaurant as React.ComponentType<any>, // 🍔 SnackShack - Hamburger
  local_fire_department: MaterialIcons.LocalFireDepartment as React.ComponentType<any>, // 🍟 SnackMachine - Fries
  smile: MaterialIcons.Smile as React.ComponentType<any>, // 😊 Happy UI Hub
  sad: MaterialIcons.Sad as React.ComponentType<any>, // 😢 Sad UI Hub
  content_paste_go: MaterialIcons.ContentPasteGo as React.ComponentType<any>, // 💥 Clipboard boom
};

interface IconProps {
  name: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  color?: string;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export const Icon: React.FC<IconProps> = ({
  name,
  size = 'md',
  className = '',
  color,
  onClick,
  style,
}) => {
  const IconComponent = iconMap[name];

  if (!IconComponent) {
    console.warn(`Icon "${name}" not found in iconMap`);
    return null;
  }

  const fontSize = sizeMap[size];

  return (
    <IconComponent
      className={`icon icon-${size} ${className}`}
      style={{
        fontSize,
        color,
        ...style,
      }}
      onClick={onClick}
    />
  );
};

// Convenience component for backward compatibility
export const MaterialIcon: React.FC<IconProps> = Icon;

// Export icon map for reference
export { iconMap };
