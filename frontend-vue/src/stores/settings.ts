/**
 * @module stores/settings
 * @description Global settings — font, size, palette, light/dark.
 * Ported from useGlobalSettings.ts (React).
 */
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type FontStyle = 'inter' | 'system' | 'mono'
export type Palette = 'default' | 'ocean' | 'forest' | 'sunset'
export type ThemeMode = 'light' | 'dark' | 'auto'

export const useSettingsStore = defineStore('settings', () => {
  const fontStyle = ref<FontStyle>('inter')
  const fontSize = ref<number>(16)
  const palette = ref<Palette>('default')
  const themeMode = ref<ThemeMode>('auto')

  function setFontStyle(style: FontStyle) {
    fontStyle.value = style
  }

  function setFontSize(size: number) {
    fontSize.value = Math.max(12, Math.min(24, size))
  }

  function setPalette(p: Palette) {
    palette.value = p
  }

  function setThemeMode(mode: ThemeMode) {
    themeMode.value = mode
  }

  function applyTheme() {
    const root = document.documentElement
    root.style.setProperty('--usx-font-size-base', `${fontSize.value}px`)
    root.setAttribute('data-theme', themeMode.value)
    root.setAttribute('data-palette', palette.value)
    root.setAttribute('data-font', fontStyle.value)
  }

  watch([fontStyle, fontSize, palette, themeMode], applyTheme, { immediate: true })

  return {
    fontStyle,
    fontSize,
    palette,
    themeMode,
    setFontStyle,
    setFontSize,
    setPalette,
    setThemeMode,
    applyTheme,
  }
}, {
  persist: true,
})
