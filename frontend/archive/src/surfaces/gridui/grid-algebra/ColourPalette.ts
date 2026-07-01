/* ═══════════════════════════════════════════════════════════════════
   ColourPalette — Unified Bootstrap/GitHub Dark palette
   ═══════════════════════════════════════════════════════════════════
   Single unified palette for both Teletext and Terminal views.
   Maps teletext colour indices (0-7) to modern colours:
     0 Black   → #0d1117 (GitHub dark bg)
     1 Red     → #da3633 (Bootstrap danger)
     2 Green   → #238636 (Bootstrap success)
     3 Yellow  → #d29922 (Bootstrap warning)
     4 Blue    → #58a6ff (Bootstrap primary)
     5 Magenta → #bc8cff (Bootstrap purple)
     6 Cyan    → #39d2c0 (Bootstrap info)
     7 White   → #e6edf3 (GitHub text primary)
   ═══════════════════════════════════════════════════════════════════ */

export type PaletteId = 'unified'

export interface Palette {
  id: PaletteId
  name: string
  colors: string[]
}

// ─── Unified Palette ──────────────────────────────────────────────────

export const UNIFIED_PALETTE: Palette = {
  id: 'unified',
  name: 'Unified Dark',
  colors: [
    '#0d1117', // 0: Black   → GitHub dark background
    '#da3633', // 1: Red     → Bootstrap danger
    '#238636', // 2: Green   → Bootstrap success
    '#d29922', // 3: Yellow  → Bootstrap warning
    '#58a6ff', // 4: Blue    → Bootstrap primary
    '#bc8cff', // 5: Magenta → Bootstrap purple
    '#39d2c0', // 6: Cyan    → Bootstrap info
    '#e6edf3', // 7: White   → GitHub text primary
  ],
}

export const PALETTES: Record<PaletteId, Palette> = {
  unified: UNIFIED_PALETTE,
}

// ─── Palette List (for UI) ───────────────────────────────────────────

export const PALETTE_LIST: Palette[] = [UNIFIED_PALETTE]

// ─── Colour Mapping ──────────────────────────────────────────────────

/**
 * Get a hex colour from the unified palette by index.
 * Clamps index to palette bounds.
 */
export function getColor(palette: PaletteId, index: number): string {
  const colors = PALETTES[palette].colors
  return colors[Math.max(0, Math.min(index, colors.length - 1))]
}

// ─── Colour Utilities ────────────────────────────────────────────────

export function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace('#', '')
  return [
    parseInt(h.substring(0, 2), 16),
    parseInt(h.substring(2, 4), 16),
    parseInt(h.substring(4, 6), 16),
  ]
}
