import { useState, useCallback } from 'react'

export interface SnackbarMessage {
  id: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'error'
  duration?: number
}

interface SurfaceStore {
  snackbar: SnackbarMessage[]
  showSnackbar: (msg: Omit<SnackbarMessage, 'id'>) => void
  dismissSnackbar: (id: string) => void
}

let snackbarCounter = 0

export function useSurfaceStore(): SurfaceStore {
  const [snackbar, setSnackbar] = useState<SnackbarMessage[]>([])

  const showSnackbar = useCallback((msg: Omit<SnackbarMessage, 'id'>) => {
    const id = `snack-${++snackbarCounter}`
    setSnackbar(prev => [...prev, { ...msg, id }])
    const duration = msg.duration ?? 4000
    if (duration > 0) {
      setTimeout(() => {
        setSnackbar(prev => prev.filter(m => m.id !== id))
      }, duration)
    }
  }, [])

  const dismissSnackbar = useCallback((id: string) => {
    setSnackbar(prev => prev.filter(m => m.id !== id))
  }, [])

  return { snackbar, showSnackbar, dismissSnackbar }
}
