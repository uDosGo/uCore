/**
 * useTheme.ts — USX Theme Manager
 *
 * Applies theme via :root class + data-theme attribute.
 * Persists to localStorage. Exposes reactive current theme.
 *
 * Usage:
 *   const { theme, setTheme, toggleDarkMode, availableThemes } = useTheme()
 */
import { ref, watch } from 'vue'

export type Theme = 'light' | 'dark' | 'teletext' | 'c64' | 'high-contrast'

const THEME_KEY = 'usx-theme'

const availableThemes: Theme[] = [
  'light',
  'dark',
  'teletext',
  'c64',
  'high-contrast',
]

// Singleton state — shared across all composable instances
const current = ref<Theme>(loadTheme())

function loadTheme(): Theme {
  try {
    const stored = localStorage.getItem(THEME_KEY)
    if (stored && availableThemes.includes(stored as Theme)) {
      return stored as Theme
    }
  } catch {
    // localStorage unavailable (SSR / privacy mode)
  }

  // Detect system preference
  if (
    typeof window !== 'undefined'
    && window.matchMedia('(prefers-color-scheme: dark)').matches
  ) {
    return 'dark'
  }

  return 'light'
}

function applyTheme(theme: Theme): void {
  if (typeof document === 'undefined') return

  const root = document.documentElement

  // Remove all theme classes
  root.classList.remove(...availableThemes)

  // Apply new theme
  if (theme !== 'light') {
    root.classList.add(theme)
  }
  root.setAttribute('data-theme', theme)

  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    // ignore
  }

  current.value = theme
}

// Apply on load
if (typeof document !== 'undefined') {
  applyTheme(current.value)
}

export function useTheme() {
  function setTheme(theme: Theme): void {
    applyTheme(theme)
  }

  function toggleDarkMode(): void {
    const next = current.value === 'dark' ? 'light' : 'dark'
    applyTheme(next)
  }

  function cycleTheme(): Theme {
    const idx = availableThemes.indexOf(current.value)
    const next = availableThemes[(idx + 1) % availableThemes.length]
    applyTheme(next)
    return next
  }

  // Listen for system preference changes
  if (typeof window !== 'undefined') {
    watch(
      current,
      () => {
        // Reactively synced — no-op needed, applyTheme already did the work
      },
      { immediate: false },
    )

    window
      .matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', (e) => {
        // Only auto-switch if user hasn't explicitly set a theme
        const stored = localStorage.getItem(THEME_KEY)
        if (!stored) {
          applyTheme(e.matches ? 'dark' : 'light')
        }
      })
  }

  return {
    theme: current,
    setTheme,
    toggleDarkMode,
    cycleTheme,
    availableThemes,
  }
}