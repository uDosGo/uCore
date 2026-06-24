/* ═══════════════════════════════════════════════════════════════════
   SurfaceShellContext — Shared state across all surfaces
   ═══════════════════════════════════════════════════════════════════
   Provides unified Vault sidebar, Chat panel, and last-surface
   navigation state so these persist across surface transitions.
   ═══════════════════════════════════════════════════════════════════ */
import React, { createContext, useContext, useState, useCallback } from 'react'

// ─── Types ──────────────────────────────────────────────────────────
export interface LastSurface {
  path: string
  tab?: string
}

interface SurfaceShellContextValue {
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  chatOpen: boolean
  setChatOpen: (open: boolean) => void
  toggleChat: () => void
  lastSurface: LastSurface | null
  setLastSurface: (surface: LastSurface | null) => void
}

// ─── Context ────────────────────────────────────────────────────────
const SurfaceShellContext = createContext<SurfaceShellContextValue>(null!)

export function useSurfaceShell() {
  return useContext(SurfaceShellContext)
}

// ─── Provider ───────────────────────────────────────────────────────
export function SurfaceShellProvider({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)
  const [lastSurface, setLastSurface] = useState<LastSurface | null>(null)

  const toggleSidebar = useCallback(() => {
    setSidebarOpen(prev => !prev)
  }, [])

  const toggleChat = useCallback(() => {
    setChatOpen(prev => !prev)
  }, [])

  return (
    <SurfaceShellContext.Provider
      value={{
        sidebarOpen,
        setSidebarOpen,
        toggleSidebar,
        chatOpen,
        setChatOpen,
        toggleChat,
        lastSurface,
        setLastSurface,
      }}
    >
      {children}
    </SurfaceShellContext.Provider>
  )
}

export default SurfaceShellContext
