/* ═══════════════════════════════════════════════════════════════════
   useDevMode — Dynamic Dev Mode detection and control
   ═══════════════════════════════════════════════════════════════════
   Probes the dev server (http://localhost:5173/developer) to detect
   if it's running. Provides toggle to start/stop the dev server.
   Has an initial probing window to avoid false negatives on first load.
   ═══════════════════════════════════════════════════════════════════ */
import { useState, useEffect, useCallback, createContext, useContext } from 'react'

const DEV_SERVER_URL = 'http://localhost:5173/developer'
const SNACKBAR_API = 'http://localhost:8484'
const POLL_INTERVAL_MS = 4000
const INITIAL_PROBE_ATTEMPTS = 5

interface DevModeContextValue {
  devServerRunning: boolean
  probing: boolean
  loading: boolean
  toggleDevMode: () => Promise<void>
}

const DevModeContext = createContext<DevModeContextValue>({
  devServerRunning: false,
  probing: true,
  loading: false,
  toggleDevMode: async () => {},
})

export const DevModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [devServerRunning, setDevServerRunning] = useState(false)
  const [loading, setLoading] = useState(false)
  const [probeCount, setProbeCount] = useState(0)
  const probing = probeCount < INITIAL_PROBE_ATTEMPTS

  // Probe dev server
  const probe = useCallback(async () => {
    try {
      const res = await fetch(DEV_SERVER_URL, {
        method: 'HEAD',
        signal: AbortSignal.timeout(2000),
      })
      const running = res.ok || res.status < 500
      if (running) setDevServerRunning(true)
      setProbeCount(p => p + 1)
      return running
    } catch {
      setProbeCount(p => p + 1)
      setDevServerRunning(false)
      return false
    }
  }, [])

  // Active polling: poll fast initially, slow down once running
  useEffect(() => {
    let cancelled = false
    let interval: ReturnType<typeof setInterval>

    async function start() {
      const isRunning = await probe()
      if (cancelled) return
      if (isRunning) {
        // Slow poll when running
        interval = setInterval(() => { if (!cancelled) void probe() }, POLL_INTERVAL_MS)
      } else if (probeCount < INITIAL_PROBE_ATTEMPTS) {
        // Fast poll during initial probing window
        interval = setInterval(() => { if (!cancelled) void probe() }, 1000)
      } else {
        // Slow poll after initial window
        interval = setInterval(() => { if (!cancelled) void probe() }, POLL_INTERVAL_MS)
      }
    }

    void start()
    return () => { cancelled = true; if (interval) clearInterval(interval) }
  }, [probe, probeCount])

  const toggleDevMode = useCallback(async () => {
    setLoading(true)
    try {
      if (devServerRunning) {
        await fetch(`${SNACKBAR_API}/api/developer/stop`, {
          method: 'POST',
          signal: AbortSignal.timeout(5000),
        }).catch(() => {})
        setDevServerRunning(false)
      } else {
        await fetch(`${SNACKBAR_API}/api/developer/start`, {
          method: 'POST',
          signal: AbortSignal.timeout(5000),
        }).catch(() => {})
        setTimeout(() => void probe(), 2000)
      }
    } finally {
      setLoading(false)
    }
  }, [devServerRunning, probe])

  return (
    <DevModeContext.Provider value={{ devServerRunning, probing, loading, toggleDevMode }}>
      {children}
    </DevModeContext.Provider>
  )
}

export function useDevMode() {
  return useContext(DevModeContext)
}