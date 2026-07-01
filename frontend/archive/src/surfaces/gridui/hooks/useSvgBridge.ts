/* ═══════════════════════════════════════════════════════════════════
   useSvgBridge — React hook for Snackbar SVG/uVector endpoints
   ═══════════════════════════════════════════════════════════════════
   Provides typed access to:
     - /api/svg/convert   — SVG → CELX/ASCII/describe/PNG
     - /api/svg/generate  — Text prompt → SVG
     - /api/svg/describe  — SVG → natural language description

   Each method returns { data, loading, error } and handles
   Snackbar connectivity gracefully (returns fallback on failure).
   ═══════════════════════════════════════════════════════════════════ */

import { useState, useCallback } from 'react'

const SNACKBAR_URL = 'http://127.0.0.1:8484'

// ─── Types ──────────────────────────────────────────────────────────

export type SvgConvertFormat = 'celx' | 'ascii' | 'describe' | 'png'

export interface SvgConvertResult {
  output: string
  format: SvgConvertFormat
  error?: string
}

export interface SvgGenerateResult {
  svg: string
  style: string
  width: number
  height: number
  element_count: number
  description: string
  error?: string
}

export interface SvgDescribeResult {
  description: string
  error?: string
}

export type SvgGenerateStyle =
  | 'full_color'
  | 'mono_chrome'
  | 'teletext'
  | 'pixel_art'
  | 'line_art'

export interface SvgGenerateOptions {
  prompt: string
  style?: SvgGenerateStyle
  width?: number
  height?: number
  background?: boolean
  extra?: string
}

// ─── Hook ───────────────────────────────────────────────────────────

export function useSvgBridge() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /** Convert SVG to another format (CELX, ASCII, describe, PNG). */
  const convert = useCallback(async (
    svg: string,
    format: SvgConvertFormat = 'celx',
  ): Promise<SvgConvertResult | null> => {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(`${SNACKBAR_URL}/api/svg/convert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ svg, format }),
      })
      if (!resp.ok) {
        const errText = await resp.text().catch(() => 'Unknown error')
        setError(`SVG convert failed (${resp.status}): ${errText}`)
        return null
      }
      const data: SvgConvertResult = await resp.json()
      return data
    } catch (err: any) {
      const msg = `SVG convert error: ${err?.message || err}`
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  /** Generate SVG from a text prompt. */
  const generate = useCallback(async (
    options: SvgGenerateOptions,
  ): Promise<SvgGenerateResult | null> => {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(`${SNACKBAR_URL}/api/svg/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: options.prompt,
          style: options.style ?? 'full_color',
          width: options.width ?? 800,
          height: options.height ?? 600,
          background: options.background ?? true,
          extra: options.extra ?? '',
        }),
      })
      if (!resp.ok) {
        const errText = await resp.text().catch(() => 'Unknown error')
        setError(`SVG generate failed (${resp.status}): ${errText}`)
        return null
      }
      const data: SvgGenerateResult = await resp.json()
      return data
    } catch (err: any) {
      const msg = `SVG generate error: ${err?.message || err}`
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  /** Describe SVG content in natural language. */
  const describe = useCallback(async (
    svg: string,
  ): Promise<SvgDescribeResult | null> => {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(`${SNACKBAR_URL}/api/svg/describe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ svg }),
      })
      if (!resp.ok) {
        const errText = await resp.text().catch(() => 'Unknown error')
        setError(`SVG describe failed (${resp.status}): ${errText}`)
        return null
      }
      const data: SvgDescribeResult = await resp.json()
      return data
    } catch (err: any) {
      const msg = `SVG describe error: ${err?.message || err}`
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  /** Check if the SVG bridge is available (Snackbar health check). */
  const isAvailable = useCallback(async (): Promise<boolean> => {
    try {
      const resp = await fetch(`${SNACKBAR_URL}/api/health`, { signal: AbortSignal.timeout(2000) })
      return resp.ok
    } catch {
      return false
    }
  }, [])

  return {
    convert,
    generate,
    describe,
    isAvailable,
    loading,
    error,
  }
}
