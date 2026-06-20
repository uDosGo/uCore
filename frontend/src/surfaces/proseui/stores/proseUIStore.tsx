/* ═══════════════════════════════════════════════════════════════════
   proseUIStore — React state for ProseUISurface
   Uses CSS palette classes from @usx/palettes/base.css instead of inline M3 tokens.
   ═══════════════════════════════════════════════════════════════════ */
import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react'

export type FontStyle = 'sans' | 'serif' | 'mono'

/** A palette entry — maps to a CSS class like .palette-paper */
export interface PaletteEntry {
  id: string
  label: string
  /** CSS class name, e.g. "palette-paper" */
  cssClass: string
  /** Light background colour for swatch preview */
  lightBg: string
  /** Light accent colour for swatch preview */
  lightAccent: string
  /** Dark background colour for swatch preview */
  darkBg: string
  /** Dark accent colour for swatch preview */
  darkAccent: string
}

export type ThemeMode = 'light' | 'dark'

export interface ChatMessage { role: 'user' | 'assistant'; content: string }

export type SnackbarType = 'info' | 'success' | 'error' | 'warning'

export interface SnackbarMessage {
  message: string
  type: SnackbarType
  action?: string
  duration?: number
}

export interface ProseUIStoreValue {
  palette: PaletteEntry
  setPalette: (p: PaletteEntry) => void
  palettes: PaletteEntry[]
  themeMode: ThemeMode
  toggleTheme: () => void
  fontSize: number
  setFontSize: (size: number) => void
  increaseFont: () => void
  decreaseFont: () => void
  fontStyle: FontStyle
  setFontStyle: (style: FontStyle) => void
  cycleFontStyle: () => void
  activeView: string
  setActiveView: (v: string) => void
  chatOpen: boolean
  toggleChat: () => void
  chatMessages: ChatMessage[]
  chatInput: string
  setChatInput: (v: string) => void
  sendChat: () => void
  /** Selected document for the editor detail panel (Kanban/Table click) */
  selectedDoc: { title: string; type: string; status: string; date: string } | null
  setSelectedDoc: (doc: { title: string; type: string; status: string; date: string } | null) => void
  /** Active chat agent */
  activeAgent: { id: string; name: string } | null
  /** Snackbar notifications (macOS growl-style) */
  snackbar: SnackbarMessage | null
  showSnackbar: (msg: SnackbarMessage) => void
  showToast: (message: string, type?: SnackbarType, duration?: number) => void
  dismissSnackbar: () => void
}

const PALETTES: PaletteEntry[] = [
  {
    id: 'paper',
    label: 'Paper',
    cssClass: 'palette-paper',
    lightBg: '#faf6ef',
    lightAccent: '#5c4a32',
    darkBg: '#1a1612',
    darkAccent: '#c49a6c',
  },
  {
    id: 'parchment',
    label: 'Parchment',
    cssClass: 'palette-parchment',
    lightBg: '#f5ecd6',
    lightAccent: '#5c4a32',
    darkBg: '#1e1812',
    darkAccent: '#d4845a',
  },
  {
    id: 'modern',
    label: 'Modern',
    cssClass: 'palette-modern',
    lightBg: '#ffffff',
    lightAccent: '#1a73e8',
    darkBg: '#0f172a',
    darkAccent: '#60a5fa',
  },
  {
    id: 'forest',
    label: 'Forest',
    cssClass: 'palette-forest',
    lightBg: '#f0f7f0',
    lightAccent: '#2d6a4f',
    darkBg: '#0f1a0f',
    darkAccent: '#52b788',
  },
  {
    id: 'sunset',
    label: 'Sunset',
    cssClass: 'palette-sunset',
    lightBg: '#fef0e8',
    lightAccent: '#c2410c',
    darkBg: '#1e1410',
    darkAccent: '#f97316',
  },
  {
    id: 'notion',
    label: 'Notion',
    cssClass: 'palette-notion',
    lightBg: '#ffffff',
    lightAccent: '#37352f',
    darkBg: '#121212',
    darkAccent: '#bb86fc',
  },
  {
    id: 'dark',
    label: 'Dark',
    cssClass: 'palette-dark',
    lightBg: '#ffffff',
    lightAccent: '#bb86fc',
    darkBg: '#121212',
    darkAccent: '#bb86fc',
  },
]

const ProseUIContext = createContext<ProseUIStoreValue | undefined>(undefined)

const STORAGE_KEY = 'proseui-prefs'
const STORAGE_VERSION = 3

interface PersistedPrefs {
  paletteId: string
  themeMode: ThemeMode
  fontSize: number
  fontStyle: FontStyle
  version?: number
}

function loadPrefs(): PersistedPrefs | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as PersistedPrefs
    // Invalidate old cached preferences on version bump
    if (!parsed.version || parsed.version < STORAGE_VERSION) {
      localStorage.removeItem(STORAGE_KEY)
      return null
    }
    return parsed
  } catch {
    return null
  }
}

function savePrefs(prefs: PersistedPrefs) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...prefs, version: STORAGE_VERSION }))
  } catch { /* quota exceeded, ignore */ }
}

function getChatResponse(text: string): string {
  const lower = text.toLowerCase()
  if (lower.includes('publish') || lower.includes('publish')) {
    return 'I can help you publish documents. Use the Editor view to write content, then click the Publish button. Or type `publish` in the command bar below.'
  }
  if (lower.includes('status') || lower.includes('how many')) {
    return 'Current workspace status: check the Board and List views for document counts.'
  }
  if (lower.includes('help')) {
    return 'I can help with:\n- **Publishing** — Ask about publishing documents\n- **Status** — Ask about workspace status\n- **Navigation** — Use the tabs in the header\n- **Editor** — Write and preview Markdown\n- **Kanban** — Drag cards between columns'
  }
  if (lower.includes('hello') || lower.includes('hi')) {
    return 'Hello! How can I help you with your workspace today?'
  }
  return `I understand you're asking about "${text}". I can help with publishing, workspace status, navigation, and more. Try asking me about "status" or "help".`
}

export const ProseUIProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const saved = loadPrefs()
  const initialPalette = saved ? PALETTES.find(p => p.id === saved.paletteId) || PALETTES[2] : PALETTES[2]
  const [palette, setPalette] = useState<PaletteEntry>(initialPalette)
  const [themeMode, setThemeMode] = useState<ThemeMode>(saved?.themeMode ?? 'dark')
  const [fontSize, setFontSize] = useState(saved?.fontSize ?? 16)
  const [fontStyle, setFontStyle] = useState<FontStyle>(saved?.fontStyle ?? 'sans')
  const [activeView, setActiveView] = useState('kanban')
  const [chatOpen, setChatOpen] = useState(true)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Hello! I can help you with documents, publishing, and more. Try asking me something.' },
  ])
  const [chatInput, setChatInput] = useState('')
  const [selectedDoc, setSelectedDoc] = useState<{ title: string; type: string; status: string; date: string } | null>(null)
  const [snackbar, setSnackbar] = useState<SnackbarMessage | null>(null)
  const snackbarTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const activeAgent = { id: 'prose-assistant', name: 'Prose Assistant' }

  const setFontSizeDirect = useCallback((size: number) => {
    setFontSize(Math.max(10, Math.min(24, size)))
  }, [])

  const increaseFont = useCallback(() => {
    setFontSize(prev => Math.min(prev + 2, 24))
  }, [])

  const decreaseFont = useCallback(() => {
    setFontSize(prev => Math.max(prev - 2, 10))
  }, [])

  const setFontStyleDirect = useCallback((style: FontStyle) => {
    setFontStyle(style)
  }, [])

  const cycleFontStyle = useCallback(() => {
    const order: FontStyle[] = ['sans', 'serif', 'mono']
    setFontStyle(prev => {
      const idx = order.indexOf(prev)
      return order[(idx + 1) % order.length]
    })
  }, [])

  const toggleTheme = useCallback(() => {
    setThemeMode(prev => prev === 'light' ? 'dark' : 'light')
  }, [])

  const toggleChat = useCallback(() => {
    setChatOpen(prev => !prev)
  }, [])

  const sendChat = useCallback(() => {
    const text = chatInput.trim()
    if (!text) return
    setChatMessages(prev => [...prev, { role: 'user', content: text }])
    setChatInput('')
    setTimeout(() => {
      setChatMessages(prev => [...prev, { role: 'assistant', content: getChatResponse(text) }])
    }, 300)
  }, [chatInput])

  const showSnackbar = useCallback((msg: SnackbarMessage) => {
    if (snackbarTimer.current) clearTimeout(snackbarTimer.current)
    setSnackbar(msg)
    const duration = msg.duration ?? 4000
    snackbarTimer.current = setTimeout(() => {
      setSnackbar(null)
      snackbarTimer.current = null
    }, duration)
  }, [])

  const showToast = useCallback((message: string, type: SnackbarType = 'info', duration: number = 4000) => {
    showSnackbar({ message, type, duration })
  }, [showSnackbar])

  const dismissSnackbar = useCallback(() => {
    if (snackbarTimer.current) clearTimeout(snackbarTimer.current)
    setSnackbar(null)
    snackbarTimer.current = null
  }, [])

  // Persist prefs whenever they change
  useEffect(() => {
    savePrefs({ paletteId: palette.id, themeMode, fontSize, fontStyle })
  }, [palette.id, themeMode, fontSize, fontStyle])

  const value: ProseUIStoreValue = {
    palette, setPalette,
    palettes: PALETTES,
    themeMode, toggleTheme,
    fontSize, setFontSize: setFontSizeDirect, increaseFont, decreaseFont,
    fontStyle, setFontStyle: setFontStyleDirect, cycleFontStyle,
    activeView, setActiveView,
    chatOpen, toggleChat,
    chatMessages, chatInput, setChatInput, sendChat,
    selectedDoc, setSelectedDoc,
    activeAgent,
    snackbar, showSnackbar, showToast, dismissSnackbar,
  }

  return (
    <ProseUIContext.Provider value={value}>
      {children}
    </ProseUIContext.Provider>
  )
}

export const useProseUIStore = (): ProseUIStoreValue => {
  const context = useContext(ProseUIContext)
  if (!context) throw new Error('useProseUIStore must be used within ProseUIProvider')
  return context
}
