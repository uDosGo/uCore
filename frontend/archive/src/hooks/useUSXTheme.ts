import { useState, useCallback } from 'react'

export interface USXThemeStyle {
  mode: 'dark' | 'light'
  primary: string
  accent: string
  fontSize: number
}

const defaultStyle: USXThemeStyle = {
  mode: 'dark',
  primary: '#58a6ff',
  accent: '#3fb950',
  fontSize: 14,
}

export function useUSXTheme() {
  const [style, setStyleState] = useState<USXThemeStyle>(defaultStyle)

  const setStyle = useCallback((partial: Partial<USXThemeStyle>) => {
    setStyleState(prev => ({ ...prev, ...partial }))
  }, [])

  return { style, setStyle }
}
