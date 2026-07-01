/* ═══════════════════════════════════════════════════════════════════
   FontResolver — Maps fontId → CSS font-family values
   ═══════════════════════════════════════════════════════════════════
   Resolves font identifiers to CSS font-family strings and
   provides per-font size scaling for grid cell rendering.

   Fonts are loaded from Google Fonts CDN (see index.html):
     - Press Start 2P  → Terminal / arcade pixel
     - VT323           → Teletext / terminal pixel

   Ported from: frontend/archive/src/surfaces/gridui/grid-algebra/FontResolver.ts
   ═══════════════════════════════════════════════════════════════════ */

export type FontCategory = 'retro' | 'modern'
export type GridFont = 'pressstart2p' | 'vt323'

export interface FontConfig {
  id: string
  name: string
  category: FontCategory
  cssFamily: string
  isBitmap: boolean
  cellSize?: [number, number]
  fallback: boolean
  fontSizeScale: number
}

// ─── Google Fonts (loaded via CDN in index.html) ──────────────

export const DEFAULT_FONTS: FontConfig[] = [
  {
    id: 'pressstart2p',
    name: 'Press Start 2P',
    category: 'retro',
    cssFamily: "'Press Start 2P', 'Courier New', monospace",
    isBitmap: true,
    cellSize: [8, 8],
    fallback: false,
    fontSizeScale: 0.65,
  },
  {
    id: 'vt323',
    name: 'VT323',
    category: 'retro',
    cssFamily: "'VT323', 'Courier New', monospace",
    isBitmap: true,
    cellSize: [8, 16],
    fallback: true,
    fontSizeScale: 1.0,
  },
]

// ─── Lookup ────────────────────────────────────────────────────

const fontMap = new Map<string, FontConfig>()
for (const f of DEFAULT_FONTS) fontMap.set(f.id, f)

export function getFont(id: string): FontConfig | undefined {
  return fontMap.get(id)
}

export function getFontFamily(id: GridFont): string {
  return fontMap.get(id)?.cssFamily ?? "'Courier New', monospace"
}

export function getFontSizeScale(id: GridFont): number {
  return fontMap.get(id)?.fontSizeScale ?? 1.0
}
