import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

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

interface USXThemeContextValue {
  style: USXThemeStyle
  setStyle: (partial: Partial<USXThemeStyle>) => void
}

const USXThemeContext = createContext<USXThemeContextValue>({
  style: defaultStyle,
  setStyle: () => {},
})

export const USXThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [style, setStyleState] = useState<USXThemeStyle>(defaultStyle)

  const setStyle = useCallback((partial: Partial<USXThemeStyle>) => {
    setStyleState(prev => ({ ...prev, ...partial }))
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', style.mode)
  }, [style.mode])

  return (
    <USXThemeContext.Provider value={{ style, setStyle }}>
      {children}
    </USXThemeContext.Provider>
  )
}

export const useUSXTheme = () => useContext(USXThemeContext)
