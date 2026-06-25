/* ═══════════════════════════════════════════════════════════════════
   useGridCoreSettings — GridCore Grid Algebra & Cell Settings
   ═══════════════════════════════════════════════════════════════════
   Independent grid algebra configuration for GridCore embeddable blocks
   (grid, teletext, terminal). Separate from USX styling system.
   Controls cell dimensions, grid density, rendering, and glyphs.
   ═══════════════════════════════════════════════════════════════════ */
import { useState, useEffect, useCallback } from 'react'

export interface GridCoreSettings {
  cellWidth: number // pixels, 8-20
  cellHeight: number // pixels, 12-32
  gridDensity: 'compact' | 'normal' | 'spacious' // affects character map
  fontFamily: 'default' | 'monospace-narrow' | 'monospace-wide'
  glyphSet: 'ascii' | 'extended' | 'unicode'
  renderMode: 'canvas' | 'dom' | 'hybrid'
  antialias: boolean
  smoothScroll: boolean
  enableAnimations: boolean
}

const SETTINGS_KEY = 'ucore-gridcore-settings-v1'

const DEFAULT_SETTINGS: GridCoreSettings = {
  cellWidth: 9,
  cellHeight: 16,
  gridDensity: 'normal',
  fontFamily: 'default',
  glyphSet: 'ascii',
  renderMode: 'canvas',
  antialias: true,
  smoothScroll: false,
  enableAnimations: true,
}

function loadSettings(): GridCoreSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
    }
  } catch {
    /* ignore */
  }
  return { ...DEFAULT_SETTINGS }
}

function saveSettings(settings: GridCoreSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  applyGridCoreSettings(settings)
}

export function applyGridCoreSettings(settings: GridCoreSettings) {
  const root = document.documentElement

  // Apply cell dimensions
  root.style.setProperty('--gridcore-cell-width', `${settings.cellWidth}px`)
  root.style.setProperty('--gridcore-cell-height', `${settings.cellHeight}px`)
  root.setAttribute('data-gridcore-cell-size', `${settings.cellWidth}x${settings.cellHeight}`)

  // Apply grid density
  root.setAttribute('data-gridcore-density', settings.gridDensity)
  const densityScale = {
    compact: 0.9,
    normal: 1.0,
    spacious: 1.1,
  }
  root.style.setProperty('--gridcore-density-scale', densityScale[settings.gridDensity].toFixed(2))

  // Apply font family
  root.setAttribute('data-gridcore-font', settings.fontFamily)

  // Apply glyph set
  root.setAttribute('data-gridcore-glyphs', settings.glyphSet)

  // Apply render mode
  root.setAttribute('data-gridcore-render', settings.renderMode)

  // Apply rendering options
  root.style.setProperty('--gridcore-antialias', settings.antialias ? '1' : '0')
  root.style.setProperty('--gridcore-smooth-scroll', settings.smoothScroll ? '1' : '0')
  root.style.setProperty('--gridcore-animations', settings.enableAnimations ? '1' : '0')
}

export function useGridCoreSettings() {
  const [settings, setSettings] = useState<GridCoreSettings>(DEFAULT_SETTINGS)
  const [isLoaded, setIsLoaded] = useState(false)

  // Load settings on mount
  useEffect(() => {
    const loaded = loadSettings()
    setSettings(loaded)
    applyGridCoreSettings(loaded)
    setIsLoaded(true)
  }, [])

  const updateSetting = useCallback(<K extends keyof GridCoreSettings>(key: K, value: GridCoreSettings[K]) => {
    setSettings(prev => {
      const next = { ...prev, [key]: value }
      saveSettings(next)
      return next
    })
  }, [])

  const resetToDefaults = useCallback(() => {
    const defaults = { ...DEFAULT_SETTINGS }
    setSettings(defaults)
    saveSettings(defaults)
  }, [])

  const presets = {
    compact: { cellWidth: 8, cellHeight: 14, gridDensity: 'compact' as const },
    normal: { cellWidth: 9, cellHeight: 16, gridDensity: 'normal' as const },
    spacious: { cellWidth: 10, cellHeight: 18, gridDensity: 'spacious' as const },
    hd: { cellWidth: 12, cellHeight: 20, gridDensity: 'normal' as const },
    retro: { cellWidth: 8, cellHeight: 16, gridDensity: 'compact' as const, glyphSet: 'ascii' as const },
  }

  const applyPreset = useCallback((presetName: keyof typeof presets) => {
    const preset = presets[presetName]
    const next = { ...settings, ...preset }
    setSettings(next)
    saveSettings(next)
  }, [settings])

  return {
    settings,
    isLoaded,
    updateSetting,
    resetToDefaults,
    applyPreset,
    presets,
  }
}
