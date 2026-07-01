/* ═══════════════════════════════════════════════════════════════════
   useSystemVariables — Hook for reading/writing system $Variables
   Connects to /api/variables backend endpoints.
   Used by Story Forms and System Pages to bind variables.
   ═══════════════════════════════════════════════════════════════════ */
import { useState, useEffect, useCallback } from 'react'

const SNACKBAR_API = 'http://localhost:8484'

interface UserVariables {
  username: string
  role: string
  location: string
  timezone: string
  uid: string
  email?: string
  [key: string]: string | undefined
}

interface InstallVariables {
  hostname: string
  platform: string
  platform_release: string
  platform_version: string
  architecture: string
  processor: string
  python_version: string
  install_date: string
  udos_root: string
  [key: string]: string
}

interface UseSystemVariablesReturn {
  userVars: UserVariables | null
  installVars: InstallVariables | null
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  updateUserVar: (key: string, value: string) => Promise<boolean>
  getVariable: (name: string) => string | undefined
  resolveTemplate: (template: string) => string
}

export function useSystemVariables(): UseSystemVariablesReturn {
  const [userVars, setUserVars] = useState<UserVariables | null>(null)
  const [installVars, setInstallVars] = useState<InstallVariables | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/variables`, {
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        const data = await res.json()
        setUserVars(data.user || {})
        setInstallVars(data.installation || {})
      } else {
        setError('Failed to fetch variables')
      }
    } catch (e) {
      setError('Network error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void refresh() }, [refresh])

  const updateUserVar = useCallback(async (key: string, value: string): Promise<boolean> => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/variables/user`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: value }),
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        await refresh()
        return true
      }
      return false
    } catch {
      return false
    }
  }, [refresh])

  /** Resolve a single variable name, checking user then install vars */
  const getVariable = useCallback((name: string): string | undefined => {
    const cleaned = name.replace(/^\$/, '')
    if (userVars && cleaned in userVars) return userVars[cleaned]
    if (installVars && cleaned in installVars) return installVars[cleaned]
    return undefined
  }, [userVars, installVars])

  /** Resolve {{variable}} or $variable placeholders in a template string */
  const resolveTemplate = useCallback((template: string): string => {
    return template
      .replace(/\{\{(\w+)\}\}/g, (_, name) => getVariable(name) || `{{${name}}}`)
      .replace(/\$(\w+)/g, (_, name) => getVariable(name) || `$${name}`)
  }, [getVariable])

  return {
    userVars,
    installVars,
    loading,
    error,
    refresh,
    updateUserVar,
    getVariable,
    resolveTemplate,
  }
}