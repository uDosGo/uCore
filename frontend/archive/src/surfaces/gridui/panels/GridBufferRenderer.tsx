/* ═══════════════════════════════════════════════════════════════════
   GridBufferRenderer — Renders a GridBuffer to DOM
   ═══════════════════════════════════════════════════════════════════
   Pure component that renders a GridBuffer as a grid of character
   cells with proper foreground/background colours.

   This is the shared renderer used by TerminalPanel, TeletextPanel,
   and GridWidget. It maps colour indices through the unified palette.

   Font selection:
     - 'teletext' mode → Bedstead (teletext-style character set)
     - 'terminal' mode → PetMe128 (C64-style character set)

   Usage:
     <GridBufferRenderer buffer={myBuffer} paletteId="unified" />
   ═══════════════════════════════════════════════════════════════════ */
import React, { useMemo } from 'react'
import { getDimensions, type GridBuffer } from '@udos/gridcore'
import { getColor } from '../grid-algebra/ColourPalette'
import type { PaletteId } from '../grid-algebra/ColourPalette'
import type { GridFont } from '../GridUIStore'

// ─── Font family map ─────────────────────────────────────────────────
const FONT_FAMILIES: Record<GridFont, string> = {
  bedstead: "'Bedstead','PetMe128','C64 User Mono','Courier New',monospace",
  petme128: "'PetMe128','C64 User Mono','Courier New',monospace",
  teletext50: "'Teletext50','PetMe128','C64 User Mono','Courier New',monospace",
  pressstart2p: "'Press Start 2P','C64 User Mono','Courier New',monospace",
}

// ─── Per-font cell size adjustments ──────────────────────────────────
// Each font has different metrics. These multipliers scale the cell
// dimensions so characters render at the correct visual size.
// Bedstead is an outline font (SAA5050 teletext) — it needs smaller
// relative font size vs pixel fonts like PetMe128 or Teletext50.
const FONT_CELL_SCALE: Record<GridFont, { widthScale: number; heightScale: number; fontSizeScale: number }> = {
  bedstead:     { widthScale: 1.0, heightScale: 1.0, fontSizeScale: 0.72 },
  petme128:     { widthScale: 1.0, heightScale: 1.0, fontSizeScale: 1.0 },
  teletext50:   { widthScale: 1.0, heightScale: 1.0, fontSizeScale: 0.85 },
  pressstart2p: { widthScale: 1.0, heightScale: 1.0, fontSizeScale: 0.65 },
}


interface GridBufferRendererProps {
  buffer: GridBuffer
  paletteId: PaletteId
  cellWidth?: number   // px per cell (default: 24 — square)
  cellHeight?: number  // px per cell (default: 24 — square)
  /** Font family override. If provided, takes precedence over gridFont. */
  fontFamily?: string
  /** GridFont from store. Defaults to 'petme128'. */
  gridFont?: GridFont
}

export const GridBufferRenderer: React.FC<GridBufferRendererProps> = ({
  buffer,
  paletteId,
  cellWidth = 24,
  cellHeight = 24,
  fontFamily,
  gridFont = 'petme128',
}) => {
  const { cols, rows } = getDimensions(buffer)

  // Resolve font: explicit fontFamily > gridFont preset > default
  const resolvedFont = fontFamily || FONT_FAMILIES[gridFont]
  // Per-font scale adjustments
  const fontScale = FONT_CELL_SCALE[gridFont]
  const adjFontSizeUnclamped = cellHeight * fontScale.fontSizeScale

  // Clamp cell sizes and font sizes to avoid sub-pixel collapse
  const MIN_CELL_PX = 4
  const clampedCellWidth = Math.max(MIN_CELL_PX, Math.round(cellWidth))
  const clampedCellHeight = Math.max(MIN_CELL_PX, Math.round(cellHeight))
  const adjFontSize = Math.max(MIN_CELL_PX, Math.round(adjFontSizeUnclamped))

  const cells = useMemo(() => {
    const result: React.ReactNode[] = []

    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cell = buffer[y][x]
        const fgColor = getColor(paletteId, cell.fg)
        const bgColor = getColor(paletteId, cell.bg)
        const key = `${y}-${x}`

        result.push(
          <span
            key={key}
            style={{
              display: 'inline-block',
              width: `${clampedCellWidth}px`,
              height: `${clampedCellHeight}px`,
              lineHeight: `${clampedCellHeight}px`,
              textAlign: 'center',
              verticalAlign: 'top',
              color: fgColor,
              backgroundColor: bgColor,
              fontWeight: cell.bold ? 'bold' : 'normal',
              opacity: cell.flash ? undefined : 1,
              animation: cell.flash ? 'teletext-flash 1s step-end infinite' : undefined,
              fontSize: `${adjFontSize}px`,
              fontFamily: resolvedFont,
              overflow: 'hidden',
              boxSizing: 'border-box',
            }}
          >
            {cell.char}
          </span>
        )
      }
    }

    return result
  }, [buffer, paletteId, cellWidth, cellHeight, cols, rows, resolvedFont, adjFontSize])


  // Use CSS grid to guarantee no gaps between cells
  const totalWidth = cols * clampedCellWidth
  const totalHeight = rows * clampedCellHeight

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${cols}, ${clampedCellWidth}px)`,
      gridTemplateRows: `repeat(${rows}, ${clampedCellHeight}px)`,
      width: totalWidth,
      height: totalHeight,
      lineHeight: 0,
      fontSize: 0,
    }}>
      {cells}
    </div>
  )
}

// ─── CSS for flash animation ─────────────────────────────────────────

export const GRID_BUFFER_RENDERER_STYLES = `
@keyframes teletext-flash {
  0%, 49% { visibility: visible; }
  50%, 100% { visibility: hidden; }
}
`
