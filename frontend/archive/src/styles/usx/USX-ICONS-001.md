# USX Icon & Font System

**Document ID:** USX-ICONS-001  
**Status:** Active, Mandatory  
**Date:** 2026-06-26  
**Replaces:** Any previous Lucide or ad-hoc icon usage  
**Source of Truth:** Google Material 3 Icons + Google Fonts

---

## Overview

The USX Icon & Font System provides a clean, modular icon system based on Google Material 3 Icons and Google Fonts for all typography.

---

## Quick Start

### 1. Import Google Fonts

Already imported in [index.html](../../index.html):

```html
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:wght@400;700&family=JetBrains+Mono:wght@400;500;600&family=Material+Icons&display=swap"
  rel="stylesheet"
/>
```

### 2. Use the Icon Component

```tsx
import { Icon } from '@/components/Icon';

export default function MyComponent() {
  return (
    <div>
      <Icon name="home" size="md" />
      <Icon name="play" size="lg" />
      <Icon name="settings" size="sm" />
    </div>
  );
}
```

### 3. Use Grid Icon Mapping

```tsx
import { gridIconMap } from '@/lib/grid-icon-mapping';

export default function MyComponent() {
  const iconName = gridIconMap.play; // 'play_arrow'
  return <Icon name={iconName} size="md" />;
}
```

---

## Icon Component

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `name` | `string` | Required | Icon name (see iconMap) |
| `size` | `'sm' \| 'md' \| 'lg' \| 'xl'` | `'md'` | Icon size in pixels |
| `className` | `string` | `''` | Additional CSS classes |
| `color` | `string` | `undefined` | Icon color |
| `onClick` | `() => void` | `undefined` | Click handler |
| `style` | `React.CSSProperties` | `{}` | Additional styles |

### Size Options

| Size | Pixels | Use Case |
|------|--------|----------|
| `sm` | 18px | Small buttons, icons in text |
| `md` | 24px | Default, standard icons |
| `lg` | 36px | Large buttons, prominent icons |
| `xl` | 48px | Hero icons, large displays |

---

## Grid Icon Mapping

The `grid-icon-mapping.ts` file maps USX concepts to Google Material 3 Icons:

```tsx
import { gridIconMap } from '@/lib/grid-icon-mapping';

// Core grid operations
gridIconMap.grid      // 'grid_view'
gridIconMap.cell      // 'crop_square'
gridIconMap.row       // 'view_column'
gridIconMap.column    // 'view_column'
gridIconMap.focus     // 'center_focus_strong'
gridIconMap.selection // 'select_all'

// Media operations
gridIconMap.play      // 'play_arrow'
gridIconMap.pause     // 'pause'
gridIconMap.stop      // 'stop'
gridIconMap.record    // 'fiber_manual_record'

// Navigation
gridIconMap.home      // 'home'
gridIconMap.search    // 'search'
gridIconMap.settings  // 'settings'
gridIconMap.user      // 'person'

// GridSmith specific
gridIconMap.gridSmith // 'grid_on'
gridIconMap.uCode     // 'code'
gridIconMap.surface   // 'surround_sound'
```

---

## Complete Icon List

### Core Grid Operations
- `grid` — grid_view
- `cell` — crop_square
- `row` — view_column
- `column` — view_column
- `focus` — center_focus_strong
- `selection` — select_all

### Media Operations
- `play` — play_arrow
- `pause` — pause
- `stop` — stop
- `record` — fiber_manual_record
- `rewind` — fast_rewind
- `forward` — fast_forward
- `volume` — volume_up
- `volumeOff` — volume_off

### Navigation
- `home` — home
- `browse` — browse_gallery
- `search` — search
- `settings` — settings
- `user` — person
- `logout` — logout
- `menu` — menu
- `close` — close
- `arrowBack` — arrow_back
- `arrowForward` — arrow_forward
- `chevronLeft` — chevron_left
- `chevronRight` — chevron_right

### Automation
- `automation` — smart_toy
- `device` — devices
- `scene` — scene
- `trigger` — bolt
- `schedule` — schedule

### File/Content
- `folder` — folder
- `file` — insert_drive_file
- `image` — image
- `video` — video_library
- `music` — music_note
- `document` — description

### Status
- `online` — wifi
- `offline` — wifi_off
- `warning` — warning
- `error` — error
- `success` — check_circle
- `pending` — pending
- `info` — info
- `help` — help

### UI Elements
- `add` — add
- `remove` — remove
- `edit` — edit
- `delete` — delete
- `save` — save
- `copy` — copy
- `paste` — paste
- `download` — download
- `upload` — upload
- `refresh` — refresh
- `share` — share
- `moreVert` — more_vert
- `star` — star
- `favorite` — favorite
- `starBorder` — star_border

### GridSmith Specific
- `gridSmith` — grid_on
- `uCode` — code
- `surface` — surround_sound
- `template` — template
- `export` — export
- `import` — import_export
- `build` — build
- `debug` — bug_report
- `test` — test
// ... (continues in file)
- `deploy` — cloud_upload
- `version` — version

---

## CSS Variables

### Icon Font

```css
:root {
  --icon-font: 'Material Icons';
}
```

### Icon Sizes

```css
:root {
  --icon-size: 24px;  /* Default size */
  --icon-size-sm: 18px;
  --icon-size-lg: 36px;
  --icon-size-xl: 48px;
}
```

---

## Audit Script

Run the audit script to verify compliance:

```bash
./scripts/audit-icons.sh
```

Expected results:
- ✅ No Lucide icons found
- ✅ No hardcoded icon strings
- ✅ Icon sizes are consistent
- ✅ Google Fonts imported
- ✅ Icon component is being used
- ✅ Grid icon mapping is being used

---

## Common Violations & Fixes

### Violation 1: Lucide Icons

**Problem:**
```tsx
import { Home, Play, Settings } from 'lucide-react';

<Home size={24} />
<Play size={24} />
<Settings size={24} />
```

**Fix:**
```tsx
import { Icon } from '@/components/Icon';

<Icon name="home" size="md" />
<Icon name="play" size="md" />
<Icon name="settings" size="md" />
```

### Violation 2: Hardcoded Icon Strings

**Problem:**
```tsx
<span className="material-icons">home</span>
<span className="material-icons" style={{ fontSize: 24 }}>play</span>
```

**Fix:**
```tsx
import { Icon } from '@/components/Icon';

<Icon name="home" size="md" />
<Icon name="play" size="md" />
```

### Violation 3: Inconsistent Icon Sizes

**Problem:**
```tsx
<Icon name="home" size={24} />  // ❌ Should use size prop
<Icon name="play" size={36} />  // ❌ Should use size prop
```

**Fix:**
```tsx
<Icon name="home" size="md" />  // ✅ Use size prop
<Icon name="play" size="lg" />  // ✅ Use size prop
```

---

## Quick Reference

```tsx
// Import
import { Icon, gridIconMap } from '@/components/Icon';
import { gridIconMap } from '@/lib/grid-icon-mapping';

// Usage
<Icon name="home" size="md" />
<Icon name="play" size="lg" />
<Icon name="settings" size="sm" />

// GridSmith mapping
const iconName = gridIconMap.gridSmith;
<Icon name={iconName} size="md" />
```

---

## Summary

| Problem | Solution |
|---------|----------|
| Lucide icons | Replaced with Google Material 3 Icons |
| Inconsistent sizes | Unified via Icon component (sm/md/lg/xl) |
| Missing/Unmapped icons | All icons mapped in grid-icon-mapping.ts |
| Hardcoded icons | Use Icon component abstraction |
| Inconsistent fonts | Google Fonts + CSS variables |

**The rule:** Always use the Icon component with size prop, never hardcode icon strings or sizes. Use grid-icon-mapping for icon names.