/* ═══════════════════════════════════════════════════════════════════
   useGlobalSettings — Unified Global Settings Hook
   ═══════════════════════════════════════════════════════════════════
   Manages synchronized Global Settings (Font Style, Base Font Size,
   Color Palette, Light/Dark Mode) across all surfaces.
   Single source of truth via localStorage.
   ═══════════════════════════════════════════════════════════════════ */
import { useState, useEffect, useCallback } from 'react'

export type FontStyle = 'inter' | 'merriweather' | 'jetbrains-mono'
export type BaseFontSize = 'xs' | 's' | 'm' | 'l' | 'xl'
export type ColorPalette = 'gh-dark' | 'pico-green' | 'pico-sunset' | 'pico-twilight'
export type LightDarkMode = 'light' | 'dark'

export interface GlobalSettings {
  fontStyle: FontStyle
  baseFontSize: BaseFontSize
  colorPalette: ColorPalette
  mode: LightDarkMode
}

const SETTINGS_KEY = 'ucore-global-settings-v3'

const FONT_SIZE_MAP: Record<BaseFontSize, number> = {
  xs: 10,
  s: 12,
  m: 14,
  l: 16,
  xl: 18,
}

const FONT_STYLE_CONFIG: Record<FontStyle, { name: string; cssVar: string }> = {
  inter: { name: 'Inter', cssVar: 'Inter, system-ui, -apple-system, sans-serif' },
  merriweather: { name: 'Merriweather', cssVar: 'Merriweather, Georgia, serif' },
  'jetbrains-mono': { name: 'JetBrains Mono', cssVar: '"JetBrains Mono", "SF Mono", monospace' },
}

const PALETTE_CONFIG: Record<ColorPalette, { name: string; light: string; dark: string }> = {
  'gh-dark': { name: 'GitHub Dark', light: '#ffffff', dark: '#0d1117' },
  'pico-green': { name: 'Pico Green', light: '#f0f6fc', dark: '#0d1117' },
  'pico-sunset': { name: 'Pico Sunset', light: '#f0f6fc', dark: '#0d1117' },
  'pico-twilight': { name: 'Pico Twilight', light: '#f0f6fc', dark: '#0d1117' },
}

const DEFAULT_SETTINGS: GlobalSettings = {
  fontStyle: 'inter',
  baseFontSize: 'm',
  colorPalette: 'gh-dark',
  mode: 'dark',
}

function loadSettings(): GlobalSettings {
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

function saveSettings(settings: GlobalSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  applyGlobalSettings(settings)
}

export function applyGlobalSettings(settings: GlobalSettings) {
  // Apply font style
  const fontStyle = FONT_STYLE_CONFIG[settings.fontStyle]
  if (fontStyle) {
    document.documentElement.style.setProperty('--usx-font-family', fontStyle.cssVar)
    document.documentElement.setAttribute('data-font-style', settings.fontStyle)
  }

  // Apply base font size
  const fontSize = FONT_SIZE_MAP[settings.baseFontSize]
  document.documentElement.style.setProperty('--usx-base-font-size', `${fontSize}px`)
  document.documentElement.setAttribute('data-base-font-size', settings.baseFontSize)

  // Apply palette and mode
  document.documentElement.setAttribute('data-palette', settings.colorPalette)
  document.documentElement.setAttribute('data-mode', settings.mode)
  document.documentElement.style.colorScheme = settings.mode
}

export function useGlobalSettings() {
  const [settings, setSettings] = useState<GlobalSettings>(DEFAULT_SETTINGS)
  const [isLoaded, setIsLoaded] = useState(false)

  // Load settings on mount
  useEffect(() => {
    const loaded = loadSettings()
    setSettings(loaded)
    applyGlobalSettings(loaded)
    setIsLoaded(true)
  }, [])

  const updateSetting = useCallback(<K extends keyof GlobalSettings>(key: K, value: GlobalSettings[K]) => {
    setSettings(prev => {
      const next = { ...prev, [key]: value }
      saveSettings(next)
      return next
    })
  }, [])

  return {
    settings,
    isLoaded,
    updateSetting,
    fontSizeMap: FONT_SIZE_MAP,
    fontStyleConfig: FONT_STYLE_CONFIG,
    paletteConfig: PALETTE_CONFIG,
  }
}
