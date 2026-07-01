/**
 * @module stores/markdown
 * @description Markdown editor state — theme, language, toolbar config.
 * Centralizes all md-editor-v3 settings for consistency across surfaces.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type EditorTheme = 'dark' | 'light'
export type EditorLanguage = 'en-US' | 'zh-CN' | 'ja-JP'

export const useMarkdownStore = defineStore('markdown', () => {
  const theme = ref<EditorTheme>('dark')
  const language = ref<EditorLanguage>('en-US')
  const fullscreen = ref(false)

  // Default toolbar set — can be overridden per-surface
  const defaultToolbars = [
    'bold', 'italic', 'strikeThrough', 'underline', '|',
    'title', 'header', 'sub', 'sup', '|',
    'quote', 'unorderedList', 'orderedList', 'task', '|',
    'codeRow', 'code', 'link', 'image', 'table', '|',
    'mermaid', 'katex', '|',
    'prettier', '|',
    'preview', 'previewOnly', 'fullscreen', 'catalog',
  ]

  function setTheme(t: EditorTheme) {
    theme.value = t
  }

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  function setLanguage(lang: EditorLanguage) {
    language.value = lang
  }

  function setFullscreen(fs: boolean) {
    fullscreen.value = fs
  }

  return {
    theme,
    language,
    fullscreen,
    defaultToolbars,
    setTheme,
    toggleTheme,
    setLanguage,
    setFullscreen,
  }
}, {
  persist: true,
})
