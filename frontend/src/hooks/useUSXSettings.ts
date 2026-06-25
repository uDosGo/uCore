/* ═══════════════════════════════════════════════════════════════════
   useUSXSettings — Developer-Controlled USX System Settings
   ═══════════════════════════════════════════════════════════════════
   Advanced USX (UI system) configuration: typography scale, spacing,
   colors, and CSS variables. Locked from Global Settings.
   Accessible only in Developer Surface > USX Settings tab.
   ═══════════════════════════════════════════════════════════════════ */
import { useState, useEffect, useCallback } from 'react'

export interface USXCSSVariables {
  [key: string]: string
}

export interface USXSettings {
  typographyScale: number // 0.8 - 1.2 multiplier
  lineHeightMultiplier: number // 1.2 - 1.8
  spacingScale: number // 0.8 - 1.2 multiplier
  borderRadius: 'sharp' | 'rounded' | 'smooth' // 0px, 4px, 8px
  shadowDepth: 'none' | 'shallow' | 'medium' | 'deep'
  customCSSVariables: USXCSSVariables
}

const SETTINGS_KEY = 'ucore-usx-settings-v1'

const DEFAULT_CSS_VARIABLES: USXCSSVariables = {
  '--usx-primary-color': '#58a6ff',
  '--usx-secondary-color': '#3fb950',
  '--usx-tertiary-color': '#d29922',
  '--usx-error-color': '#f85149',
  '--usx-warning-color': '#d29922',
  '--usx-success-color': '#3fb950',
  '--usx-info-color': '#58a6ff',
  '--usx-muted-color': '#8b949e',
  '--usx-background-color': '#0d1117',
  '--usx-surface-color': '#1c2128',
  '--usx-border-color': '#30363d',
}

const DEFAULT_SETTINGS: USXSettings = {
  typographyScale: 1,
  lineHeightMultiplier: 1.5,
  spacingScale: 1,
  borderRadius: 'rounded',
  shadowDepth: 'medium',
  customCSSVariables: { ...DEFAULT_CSS_VARIABLES },
}

function loadSettings(): USXSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        ...DEFAULT_SETTINGS,
        ...parsed,
        customCSSVariables: {
          ...DEFAULT_CSS_VARIABLES,
          ...parsed.customCSSVariables,
        },
      }
    }
  } catch {
    /* ignore */
  }
  return { ...DEFAULT_SETTINGS }
}

function saveSettings(settings: USXSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  applyUSXSettings(settings)
}

export function applyUSXSettings(settings: USXSettings) {
  const root = document.documentElement

  // Apply typography scale
  root.style.setProperty('--usx-typography-scale', settings.typographyScale.toFixed(2))

  // Apply line height
  root.style.setProperty('--usx-line-height', settings.lineHeightMultiplier.toFixed(2))

  // Apply spacing scale
  root.style.setProperty('--usx-spacing-scale', settings.spacingScale.toFixed(2))

  // Apply border radius
  const radiusMap = { sharp: '0px', rounded: '4px', smooth: '8px' }
  root.style.setProperty('--usx-border-radius', radiusMap[settings.borderRadius])
  root.setAttribute('data-border-radius', settings.borderRadius)

  // Apply shadow depth
  const shadowMap = {
    none: '0 0 0 rgba(0,0,0,0)',
    shallow: '0 1px 3px rgba(0,0,0,0.12)',
    medium: '0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)',
    deep: '0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)',
  }
  root.style.setProperty('--usx-shadow-depth', shadowMap[settings.shadowDepth])
  root.setAttribute('data-shadow-depth', settings.shadowDepth)

  // Apply custom CSS variables
  Object.entries(settings.customCSSVariables).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })
}

export function useUSXSettings() {
  const [settings, setSettings] = useState<USXSettings>(DEFAULT_SETTINGS)
  const [isLoaded, setIsLoaded] = useState(false)

  // Load settings on mount
  useEffect(() => {
    const loaded = loadSettings()
    setSettings(loaded)
    applyUSXSettings(loaded)
    setIsLoaded(true)
  }, [])

  const updateSetting = useCallback(<K extends keyof USXSettings>(key: K, value: USXSettings[K]) => {
    setSettings(prev => {
      const next = { ...prev, [key]: value }
      saveSettings(next)
      return next
    })
  }, [])

  const updateCSSVariable = useCallback((varName: string, value: string) => {
    setSettings(prev => {
      const next = {
        ...prev,
        customCSSVariables: {
          ...prev.customCSSVariables,
          [varName]: value,
        },
      }
      saveSettings(next)
      return next
    })
  }, [])

  const resetToDefaults = useCallback(() => {
    const defaults = { ...DEFAULT_SETTINGS }
    setSettings(defaults)
    saveSettings(defaults)
  }, [])

  const exportAsCSS = useCallback((): string => {
    let css = ':root {\n'
    Object.entries(settings.customCSSVariables).forEach(([key, value]) => {
      css += `  ${key}: ${value};\n`
    })
    css += `  --usx-typography-scale: ${settings.typographyScale};\n`
    css += `  --usx-line-height: ${settings.lineHeightMultiplier};\n`
    css += `  --usx-spacing-scale: ${settings.spacingScale};\n`
    css += `  --usx-border-radius: ${['sharp', 'rounded', 'smooth'].includes(settings.borderRadius) ? ['0px', '4px', '8px'][['sharp', 'rounded', 'smooth'].indexOf(settings.borderRadius)] : '4px'};\n`
    css += '}\n'
    return css
  }, [settings])

  return {
    settings,
    isLoaded,
    updateSetting,
    updateCSSVariable,
    resetToDefaults,
    exportAsCSS,
    defaultCSSVariables: DEFAULT_CSS_VARIABLES,
  }
}
