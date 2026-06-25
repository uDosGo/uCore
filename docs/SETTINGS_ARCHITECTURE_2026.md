# Settings Architecture 2026

## Overview

The settings system has been reorganized into three independent, purpose-built layers:

1. **Global Settings** (user-facing final controls)
2. **USX Settings** (typography & styling system)
3. **GridCore Settings** (grid algebra & cell configuration)
4. **uSystem Settings** (system surface configuration)

## Architecture Layers

### Layer 1: Global Settings (System Surface)

**Location**: `http://localhost:5173/system?tab=global-settings`

**Components**:
- `GlobalSettingsPanel.tsx` — User-facing UI
- `useGlobalSettings` hook — State management

**Configuration**:
```typescript
interface GlobalSettings {
  fontStyle: 'inter' | 'merriweather' | 'jbmono'
  baseSize: 'xs' | 's' | 'm' | 'l' | 'xl'
  palette: 'github-dark' | 'palette-2' | 'palette-3' | 'palette-4'
  lightMode: boolean
}
```

**Storage**: `localStorage:globalSettings`

**CSS Variables Applied**:
- `--font-family` (cascades through Pico)
- `--pico-font-size` (base typography scale)
- `--pico-primary`, `--pico-border-color` (palette colors)

**User Switchers** (4 final controls):
1. Font Style selector (3 options)
2. Base Font Size selector (5 options)
3. Color Palette selector (4 options)
4. Light/Dark Mode toggle

---

### Layer 2: USX Settings (Developer Surface)

**Location**: `http://localhost:5173/developer?tab=usx-settings`

**Components**:
- `USXSettingsPanel.tsx` — Typography, colors, CSS variables
- `useUSXSettings` hook — State management
- `usx-settings.css` — Styling
- `usx-settings.tsx` — Tabs component wrapper

**Configuration**:
```typescript
interface USXSettings {
  typography: {
    scale: 'compact' | 'normal' | 'spacious'
    lineHeight: number
    spacingMultiplier: number
  }
  colors: {
    borderRadius: 'sharp' | 'rounded' | 'pill'
    shadowDepth: 'flat' | 'subtle' | 'elevated'
  }
  customVariables: Record<string, string>
}
```

**Storage**: `localStorage:usxSettings`

**CSS Variables Managed**:
- `--usx-typography-scale`
- `--usx-spacing-*` (xs, sm, md, lg, xl, 2xl)
- `--usx-border-radius`
- `--usx-shadow-depth`
- Custom user variables

**Tabs**:
1. **Typography**: Scale selector, line height, spacing multipliers
2. **Colors**: Border radius presets, shadow depth presets
3. **Variables**: CSS variable editor with color picker & validation
4. **Stylesheet**: Live-generated CSS export button

**Features**:
- Real-time preview of typography scales
- Color picker integration
- CSS validation
- Export stylesheet as text file
- Import/export configurations

---

### Layer 3: GridCore Settings (Developer Surface)

**Location**: `http://localhost:5173/developer?tab=gridcore-settings`

**Components**:
- `GridCoreSettingsPanel.tsx` — Grid algebra controls
- `useGridCoreSettings` hook — State management
- `gridcore-settings.css` — Styling

**Configuration**:
```typescript
interface GridCoreSettings {
  preset: 'compact' | 'normal' | 'spacious' | 'hd' | 'retro'
  cellWidth: number  // 6-20px
  cellHeight: number // 10-32px
  gridDensity: number
  fontFamily: string
  glyphSet: 'ascii' | 'extended' | 'unicode'
  renderMode: 'canvas' | 'dom' | 'hybrid'
  antialiasing: boolean
  smoothScroll: boolean
  animations: boolean
}
```

**Storage**: `localStorage:gridCoreSettings`

**Features**:
- 5 quick presets
- Independent from USX (no style bleed)
- Canvas/DOM/Hybrid rendering modes
- Glyph set selection
- Performance toggles

---

### Layer 4: uSystem Settings (Developer Surface)

**Location**: `http://localhost:5173/developer?tab=usystem-settings`

**Components**:
- `uSystemSettingsPanel.tsx` — Service & monitoring setup
- `system-surface-dev.css` — Styling

**Configuration**:
```typescript
interface uSystemConfig {
  serviceUrl: string
  enableDebugLogs: boolean
  enableMetrics: boolean
  pageRefreshInterval: number
  serviceTimeout: number
  enableAnalytics: boolean
}
```

**Storage**: `localStorage:uSystemSettings`

**Sections**:
1. **Service Connection**: Backend URL, timeout configuration
2. **Performance**: Auto-refresh interval settings
3. **Monitoring & Debug**: Feature toggles for logging, metrics, analytics

---

## Data Flow

```
┌─────────────────────┐
│  Global Settings    │  User-facing final controls
│  (System Surface)   │  → useGlobalSettings hook
└──────────┬──────────┘
           │
           ├── Applies: typography cascade, palette colors, mode
           ├── Storage: localStorage:globalSettings
           └── CSS: document.documentElement.setAttribute('data-global-settings')

┌─────────────────────┐
│   USX Settings      │  Typography, spacing, custom CSS variables
│ (Developer Surface) │  → useUSXSettings hook
└──────────┬──────────┘
           │
           ├── Applies: spacing scales, border radius, shadows
           ├── Manages: live CSS variable editor
           ├── Storage: localStorage:usxSettings
           └── CSS: document.documentElement.setAttribute('data-usx-settings')

┌─────────────────────┐
│  GridCore Settings  │  Grid algebra (INDEPENDENT)
│ (Developer Surface) │  → useGridCoreSettings hook
└──────────┬──────────┘
           │
           ├── No interaction with USX or Global
           ├── Preset-driven configuration
           ├── Storage: localStorage:gridCoreSettings
           └── CSS: document.documentElement.setAttribute('data-gridcore-settings')

┌─────────────────────┐
│  uSystem Settings   │  System Surface configuration
│ (Developer Surface) │  → (localStorage only, no direct CSS)
└─────────────────────┘
```

## CSS Class Naming Conventions

### System Surface Classes (system-surface.css)
```
.system-panel              /* Base container */
.system-panel-header       /* Header with title + count */
.system-panel-title        /* Main title */
.system-panel-count        /* Item count badge */

.system-card               /* Grid card item */
.system-card-header        /* Card header area */
.system-card-icon          /* Icon in card */
.system-card-title         /* Card title */
.system-card-desc          /* Card description */

.system-filter-group       /* Filter button group */
.system-filter-btn         /* Individual filter button */
.system-filter-btn--active /* Active filter state */

.system-stats              /* Statistics row */
.system-stat               /* Individual stat */

.system-list               /* List container */
.system-list-item          /* List item */

/* Preserved gtxform/marp styling */
.gtxform-container         /* Form container */
.gtxform-field             /* Form field */
.gtxform-label             /* Form label */
.gtxform-input             /* Form input */

.marp-slide                /* Marp presentation slide */
.marp-slide-title          /* Slide title */
```

### Developer Surface Classes

#### USX Settings (usx-settings.css)
```
.developer-panel
.developer-panel-header
.developer-panel-title
.developer-search-input

/* Typography section */
.developer-typography-scale
.developer-font-selector

/* Variables editor */
.developer-css-variable-row
.developer-variable-input
.developer-color-picker
```

#### uSystem Settings (system-surface-dev.css)
```
.usystem-settings-panel
.usystem-settings-info          /* Info box */
.usystem-settings-section       /* Settings section */
.usystem-settings-section-title /* Section title */
.usystem-settings-field         /* Form field */
.usystem-settings-toggle-row    /* Toggle row */
.usystem-settings-toggle        /* Toggle switch */
```

#### GridCore Settings (gridcore-settings.css)
```
.gridcore-settings-panel
.gridcore-preset-grid
.gridcore-preset-btn
.gridcore-slider-group
.gridcore-slider-label
.gridcore-options-grid
```

## Storage & Persistence

All settings use `localStorage` with keys:
- `globalSettings`
- `usxSettings`
- `gridCoreSettings`
- `uSystemSettings`

Each hook automatically:
1. Reads from localStorage on mount
2. Writes to localStorage on change
3. Applies CSS variables to document root

## Usage in Components

### Using Global Settings
```typescript
import { useGlobalSettings } from '../../hooks/useGlobalSettings'

export function MyComponent() {
  const { fontStyle, baseSize, palette, lightMode } = useGlobalSettings()
  return <div>{fontStyle} @ {baseSize}</div>
}
```

### Using USX Settings
```typescript
import { useUSXSettings } from '../../hooks/useUSXSettings'

export function MyComponent() {
  const { typography, colors, customVariables } = useUSXSettings()
  return <div style={{ ...customVariables }}>Content</div>
}
```

### Using GridCore Settings
```typescript
import { useGridCoreSettings } from '../../hooks/useGridCoreSettings'

export function GridComponent() {
  const { preset, cellWidth, cellHeight, renderMode } = useGridCoreSettings()
  return <canvas data-gridcore={preset} />
}
```

## Integration Points

### System Surface
- **Global Settings Tab**: Final user controls
- **Pages, Tools, Services**: Use global + uSystem settings
- **Variables Panel**: uSystem managed variables

### Developer Surface
- **USX Settings Tab**: Full typography & color control
- **GridCore Settings Tab**: Grid algebra configuration
- **uSystem Settings Tab**: Service & monitoring setup
- **All other tabs**: Cascade global settings

## Migration Notes (if updating existing components)

1. **Old hardcoded colors** → Use CSS variables from palette
2. **Old font-size values** → Use `var(--pico-font-size)` + scale multipliers
3. **Old spacing** → Use `var(--usx-spacing-*)` variables
4. **Grid settings** → Use GridCore hooks (independent)

## Future Enhancements

- [ ] Settings import/export via JSON
- [ ] Settings profiles (saved configurations)
- [ ] Keyboard shortcuts for common settings
- [ ] Real-time theme preview with side-by-side comparison
- [ ] Accessibility settings panel (contrast, focus indicators)
- [ ] Performance profiling integration
