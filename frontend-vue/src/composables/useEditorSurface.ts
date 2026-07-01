/**
 * @module composables/useEditorSurface
 * @description Shared global editor surface state.
 * Allows EditorPanel to appear in any surface when a file is selected
 * from the FilepickerSidebar.
 */
import { ref, computed } from 'vue'

export interface EditorFile {
  path: string
  filename: string
  content: string
  extension: string
}

export const useEditorSurface = () => {
  const open = ref(false)
  const currentFile = ref<EditorFile | null>(null)
  const content = ref('')

  const title = computed(() => currentFile.value?.filename || 'Untitled')

  function openFile(file: EditorFile) {
    currentFile.value = file
    content.value = file.content
    open.value = true
  }

  function closeEditor() {
    open.value = false
    currentFile.value = null
    content.value = ''
  }

  function updateContent(value: string) {
    content.value = value
    if (currentFile.value) {
      currentFile.value.content = value
    }
  }

  function saveContent(value: string) {
    if (currentFile.value) {
      currentFile.value.content = value
      // TODO: Wire to backend file-save API
      console.log('[EditorSurface] File saved:', currentFile.value.path)
    }
  }

  return {
    open,
    currentFile,
    content,
    title,
    openFile,
    closeEditor,
    updateContent,
    saveContent,
  }
}

// Singleton instance for cross-component sharing
let singletonInstance: ReturnType<typeof useEditorSurface> | null = null

export function getEditorSurface() {
  if (!singletonInstance) {
    singletonInstance = useEditorSurface()
  }
  return singletonInstance
}