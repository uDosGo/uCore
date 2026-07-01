/* ══════════════════════════════════════════════════════════════════
   GridUI Store — React Hook-based state management
   ═══════════════════════════════════════════════════════════════════
   Unified surface with 3 tabs (Map, Grid, Assets) + Terminal/Teletext
   accessible via nav rail. Settings remains as modal drawer.
   ═══════════════════════════════════════════════════════════════════
   ⚠️  IMPORTANT: GridUI uses its own grid-based CSS styles that are
   intentionally SEPARATE from USX styles. Do NOT merge gridui styles
   with USX styles — they have unique rendering requirements (grid
   algebra, teletext, character maps) that conflict with USX layout.
   When updating USX, keep grid-styles in their own files.
   ═══════════════════════════════════════════════════════════════════ */
import { useState, useRef, useEffect, useCallback, useMemo, createContext, useContext } from 'react'

// ─── Types ──────────────────────────────────────────────────────────
export type GridPanelId = 'terminal' | 'teletext' | 'grid' | 'feeds'
export type GridUITab = 'map' | 'grid' | 'assets'


export type FontStyle = 'serif' | 'sans' | 'mono'
export type GridFont = 'bedstead' | 'petme128' | 'teletext50' | 'pressstart2p'
export type GridDisplayMode = 'teletext' | 'mono' | 'wireframe'
export type BorderMode = 1 | 2 | 3
export interface GridPanel { id: GridPanelId; label: string; icon: string; description: string }
export interface GridLayer { id: string; name: string; visible: boolean; zIndex: number; color: string; opacity: number }
export interface GridCell { x: number; y: number; char: string; color?: string; bgColor?: string }
export interface ViewportSettings { cols: number; rows: number; zoom: number; bgColor: string; gridColor: string; textColor: string; surfaceBgColor: string; borderMode: BorderMode; borderBgColor: string }
export interface SnackbarMessage { id: string; message: string; action?: string; duration?: number; type?: 'info' | 'success' | 'warning' | 'error' }
export interface CharEntry { index: number; char: string; codepoint: string; hasGlyph: boolean; isBlockGraphic?: boolean }
export interface FontMap { font: { filename: string; family: string }; char_128_coverage: { total: number; covered: number; missing: number; coverage_pct: number }; teletext_coverage: { total: number; covered: number; missing: number }; chars: CharEntry[]; teletext_chars: CharEntry[] }

export const PANELS: GridPanel[] = [
  { id: 'terminal', label: 'Terminal', icon: 'terminal', description: 'C64 BASIC terminal' },
  { id: 'teletext', label: 'Teletext', icon: 'tv', description: 'Ceefax teletext page viewer' },
  { id: 'grid', label: 'Grid Editor', icon: 'grid-3x3-gap-fill', description: 'USX grid layers, cell editor & character maps' },
  { id: 'feeds', label: 'Feeds', icon: 'rss_feed', description: 'Feed source configuration & management' },
]


export const VIEWPORT_PRESETS: Record<string, ViewportSettings> = {
  // 1:1 square: 28×28 → 672×672
  '28x28': { cols: 28, rows: 28, zoom: 1, bgColor: '#0d1117', gridColor: '#21262d', textColor: '#e6edf3', surfaceBgColor: '#010409', borderMode: 1, borderBgColor: '#0d1117' },
  // 4:3 approximation: 48×36 → 1152×864 = 1.333
  '48x36': { cols: 48, rows: 36, zoom: 1, bgColor: '#0d1117', gridColor: '#21262d', textColor: '#e6edf3', surfaceBgColor: '#010409', borderMode: 1, borderBgColor: '#0d1117' },
  // 16:9 approximation: 64×36 → 1536×864 = 1.777
  '64x36': { cols: 64, rows: 36, zoom: 1, bgColor: '#0d1117', gridColor: '#21262d', textColor: '#e6edf3', surfaceBgColor: '#010409', borderMode: 1, borderBgColor: '#0d1117' },
}


export const BORDER_MODE_CONFIGS: Record<BorderMode, { fillFraction: number; surfaceBg: string; borderBg: string }> = {
  1: { fillFraction: 0.90, surfaceBg: '#010409', borderBg: '#21262d' },
  2: { fillFraction: 0.95, surfaceBg: '#010409', borderBg: '#161b22' },
  3: { fillFraction: 0.99, surfaceBg: '#010409', borderBg: '#010409' },
}

export const CHAR_W = 24
export const CHAR_H = 24
const STORAGE_KEY = 'gridui-prefs'

// ─── Default viewport for each panel type ────────────────────────────
const DEFAULT_TERMINAL_VP: ViewportSettings = { ...VIEWPORT_PRESETS['64x36'] }
const DEFAULT_TELETEXT_VP: ViewportSettings = { ...VIEWPORT_PRESETS['48x36'] }


// ─── Store Hook ─────────────────────────────────────────────────────
export function useGridUIStore() {
  const [activePanel, setActivePanel] = useState<GridPanelId>('terminal')
  const [isDark, setIsDark] = useState(true)
  const [fontSize, setFontSizeState] = useState(14)
  const [fontStyle, setFontStyleState] = useState<FontStyle>('sans')
  const [gridFont, setGridFontState] = useState<GridFont>('petme128')
  // Independent viewport settings per panel type
  const [terminalViewport, setTerminalViewport] = useState<ViewportSettings>({ ...DEFAULT_TERMINAL_VP })
  const [teletextViewport, setTeletextViewport] = useState<ViewportSettings>({ ...DEFAULT_TELETEXT_VP })
  // Viewport settings popup visibility
  const [viewportPopupOpen, setViewportPopupOpen] = useState(false)
  const [gridLayers, setGridLayers] = useState<GridLayer[]>([
    { id: 'layer-0', name: 'Base Grid', visible: true, zIndex: 0, color: '#1a1a1a', opacity: 1 },
    { id: 'layer-1', name: 'System Status', visible: false, zIndex: 1, color: '#00FF00', opacity: 1 },
    { id: 'layer-2', name: 'Vault Contents', visible: false, zIndex: 2, color: '#00FFFF', opacity: 1 },
    { id: 'layer-3', name: 'Feed Items', visible: false, zIndex: 3, color: '#FFFF00', opacity: 1 },
    { id: 'layer-4', name: 'QR Storage', visible: false, zIndex: 4, color: '#FF00FF', opacity: 1 },
    { id: 'layer-5', name: 'Overlay', visible: false, zIndex: 5, color: '#FF6600', opacity: 1 },
  ])
  const [displayMode, setDisplayMode] = useState<GridDisplayMode>('teletext')
  const [gridCells, setGridCells] = useState<GridCell[]>([])
  const [navRailCollapsed, setNavRailCollapsed] = useState(false)
  const [snackbarQueue, setSnackbarQueue] = useState<SnackbarMessage[]>([])
  const [activeSnackbar, setActiveSnackbar] = useState<SnackbarMessage | null>(null)

  const activePanelMeta = useMemo(() => PANELS.find(p => p.id === activePanel), [activePanel])

  // ─── Computed: active viewport based on current panel ──────────────
  const viewport = useMemo<ViewportSettings>(() => {
    if (activePanel === 'teletext') return teletextViewport
    return terminalViewport
  }, [activePanel, terminalViewport, teletextViewport])

  const persist = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        isDark, fontSize, fontStyle,
        terminalViewport, teletextViewport,
        navRailCollapsed, displayMode
      }))
    } catch {}
  }, [isDark, fontSize, fontStyle, terminalViewport, teletextViewport, navRailCollapsed, displayMode])

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const s = JSON.parse(raw)
        if (s.isDark !== undefined) setIsDark(s.isDark)
        if (s.fontSize) setFontSizeState(s.fontSize)
        if (s.fontStyle) setFontStyleState(s.fontStyle)
        if (s.terminalViewport) setTerminalViewport(s.terminalViewport)
        if (s.teletextViewport) setTeletextViewport(s.teletextViewport)
        if (s.navRailCollapsed !== undefined) setNavRailCollapsed(s.navRailCollapsed)
        if (s.displayMode) setDisplayMode(s.displayMode)
      }
    } catch {}
  }, [])

  const toggleTheme = useCallback(() => { setIsDark(d => !d); setTimeout(persist, 0) }, [persist])
  const increaseFontSize = useCallback(() => { setFontSizeState(s => { const n = Math.min(24, s + 1); setTimeout(() => persist(), 0); return n }) }, [persist])
  const decreaseFontSize = useCallback(() => { setFontSizeState(s => { const n = Math.max(10, s - 1); setTimeout(() => persist(), 0); return n }) }, [persist])
  const setFontSize = useCallback((s: number) => { setFontSizeState(Math.max(10, Math.min(24, s))); setTimeout(persist, 0) }, [persist])
  const setFontStyle = useCallback((s: FontStyle) => { setFontStyleState(s); setTimeout(persist, 0) }, [persist])
  const setGridFont = useCallback((f: GridFont) => { setGridFontState(f); setTimeout(persist, 0) }, [persist])
  const toggleNavRail = useCallback(() => { setNavRailCollapsed(c => !c); setTimeout(persist, 0) }, [persist])
  const setGridDisplayMode = useCallback((m: GridDisplayMode) => { setDisplayMode(m); setTimeout(persist, 0) }, [persist])
  // ─── Set viewport for the currently active panel ───────────────────
  const setViewport = useCallback((settings: Partial<ViewportSettings>) => {
    const clamp = (v: Partial<ViewportSettings>) => {
      const clamped = { ...settings }
      if (clamped.cols !== undefined) clamped.cols = Math.max(24, Math.min(128, clamped.cols))
      if (clamped.rows !== undefined) clamped.rows = Math.max(4, Math.min(128, clamped.rows))
      if (clamped.borderMode !== undefined) {
        const cfg = BORDER_MODE_CONFIGS[clamped.borderMode]
        clamped.surfaceBgColor = cfg.surfaceBg
        clamped.borderBgColor = cfg.borderBg
      }
      return clamped
    }
    const next = clamp(settings)
    if (activePanel === 'teletext') {
      setTeletextViewport(v => ({ ...v, ...next }))
    } else {
      setTerminalViewport(v => ({ ...v, ...next }))
    }
    setTimeout(() => persist(), 0)
  }, [activePanel, persist])

  const applyViewportPreset = useCallback((name: string) => {
    const preset = VIEWPORT_PRESETS[name]
    if (preset) {
      const updated = { ...preset }
      const cfg = BORDER_MODE_CONFIGS[updated.borderMode]
      updated.surfaceBgColor = cfg.surfaceBg
      updated.borderBgColor = cfg.borderBg
      if (activePanel === 'teletext') {
        setTeletextViewport(updated)
      } else {
        setTerminalViewport(updated)
      }
      setTimeout(persist, 0)
    }
  }, [activePanel, persist])

  const toggleViewportPopup = useCallback(() => setViewportPopupOpen(v => !v), [])

  const toggleLayer = useCallback((layerId: string) => {
    setGridLayers(layers => layers.map(l => l.id === layerId ? { ...l, visible: !l.visible } : l))
  }, [])
  const setLayerVisibility = useCallback((layerId: string, visible: boolean) => {
    setGridLayers(layers => layers.map(l => l.id === layerId ? { ...l, visible } : l))
  }, [])
  const setLayerOpacity = useCallback((layerId: string, opacity: number) => {
    setGridLayers(layers => layers.map(l => l.id === layerId ? { ...l, opacity: Math.max(0, Math.min(1, opacity)) } : l))
  }, [])
  const addLayer = useCallback((name: string, color: string) => {
    setGridLayers(layers => {
      const maxZ = layers.reduce((max, l) => Math.max(max, l.zIndex), -1)
      return [...layers, { id: `layer-${Date.now()}`, name, visible: true, zIndex: maxZ + 1, color, opacity: 1 }]
    })
  }, [])
  const removeLayer = useCallback((layerId: string) => {
    setGridLayers(layers => layers.filter(l => l.id !== layerId))
  }, [])

  const updateCell = useCallback((x: number, y: number, updates: Partial<GridCell>) => {
    setGridCells(cells => {
      const idx = cells.findIndex(c => c.x === x && c.y === y)
      if (idx >= 0) {
        const next = [...cells]
        next[idx] = { ...next[idx], ...updates }
        return next
      }
      return [...cells, { x, y, char: ' ', ...updates }]
    })
  }, [])

  const showSnackbar = useCallback((msg: Omit<SnackbarMessage, 'id'>) => {
    const id = `snack-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`
    setSnackbarQueue(q => [...q, { ...msg, id, duration: msg.duration ?? 4000, type: msg.type ?? 'info' }])
  }, [])
  const dismissSnackbar = useCallback(() => { setActiveSnackbar(null) }, [])

  useEffect(() => {
    if (activeSnackbar || snackbarQueue.length === 0) return
    const next = snackbarQueue[0]
    setSnackbarQueue(q => q.slice(1))
    setActiveSnackbar(next)
    const timer = setTimeout(() => { setActiveSnackbar(null) }, next.duration)
    return () => clearTimeout(timer)
  }, [activeSnackbar, snackbarQueue])

  return {
    activePanel, setActivePanel, activePanelMeta,
    isDark, toggleTheme,
    fontSize, increaseFontSize, decreaseFontSize, setFontSize,
    fontStyle, setFontStyle,
    gridFont, setGridFont,
    viewport, setViewport, applyViewportPreset,
    viewportPopupOpen, toggleViewportPopup,
    terminalViewport, teletextViewport,
    gridLayers, toggleLayer, setLayerVisibility, setLayerOpacity, addLayer, removeLayer,
    displayMode, setGridDisplayMode,
    gridCells, setGridCells, updateCell,
    navRailCollapsed, toggleNavRail,
    activeSnackbar, dismissSnackbar, showSnackbar,
  }
}

export type GridUIStore = ReturnType<typeof useGridUIStore>
export const GridUIContext = createContext<GridUIStore>(null!)
export function useStore() { return useContext(GridUIContext) }
