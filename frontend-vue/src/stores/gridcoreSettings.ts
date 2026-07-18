/**
 * @module stores/gridcoreSettings
 * @description GridCore UI chrome settings. Renderer/algebra behavior stays separate.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type GridCorePreset = 'compact' | 'normal' | 'spacious' | 'hd' | 'retro'
export type GridCoreRenderMode = 'canvas' | 'dom' | 'hybrid'

export const useGridCoreSettingsStore = defineStore('gridcoreSettings', () => {
  const preset = ref<GridCorePreset>('normal')
  const cellWidth = ref(10)
  const cellHeight = ref(16)
  const renderMode = ref<GridCoreRenderMode>('hybrid')

  function setPreset(nextPreset: GridCorePreset) {
    preset.value = nextPreset
  }

  function setCellWidth(width: number) {
    cellWidth.value = Math.max(6, Math.min(20, width))
  }

  function setCellHeight(height: number) {
    cellHeight.value = Math.max(10, Math.min(32, height))
  }

  function setRenderMode(mode: GridCoreRenderMode) {
    renderMode.value = mode
  }

  return {
    preset,
    cellWidth,
    cellHeight,
    renderMode,
    setPreset,
    setCellWidth,
    setCellHeight,
    setRenderMode,
  }
}, {
  persist: true,
})
