/* ═══════════════════════════════════════════════════════════════════
   GridWidget — Embeddable grid renderer for any surface
   ═══════════════════════════════════════════════════════════════════
   A lightweight React component that renders a GridBuffer at any
   size. Can be embedded in ProseUI, Dashboard, or any other surface.
   Now accepts gridFont prop to use the store's active font.

   Usage:
     <GridWidget buffer={myBuffer} width={360} height={200} />
   ═══════════════════════════════════════════════════════════════════ */
import React, { useMemo } from 'react'
import type { GridBuffer } from '../grid-algebra/GridCell'
import { getDimensions } from '../grid-algebra/GridCell'
import { getColor } from '../grid-algebra/ColourPalette'
import type { PaletteId } from '../grid-algebra/ColourPalette'
import type { GridFont } from '../GridUIStore'

// ─── Font family map (mirrors GridBufferRenderer) ────────────────────
const FONT_FAMILIES: Record<GridFont, string> = {
  bedstead: "'Bedstead','PetMe128','C64 User Mono','Courier New',monospace",
  petme128: "'PetMe128','C64 User Mono','Courier New',monospace",
  teletext50: "'Teletext50','PetMe128','C64 User Mono','Courier New',monospace",
  pressstart2p: "'Press Start 2P','C64 User Mono','Courier New',monospace",
}

interface GridWidgetProps {
  buffer: GridBuffer
  paletteId?: PaletteId
  width?: number   // px (default: auto-fit to buffer)
  height?: number  // px (default: auto-fit to buffer)
  className?: string
  style?: React.CSSProperties
  gridFont?: GridFont  // font to use (default: 'petme128')
}

export const GridWidget: React.FC<GridWidgetProps> = ({
  buffer,
  paletteId = 'unified',
  width,
  height,
  className,
  style,
  gridFont = 'petme128',
}) => {
  const { cols, rows } = getDimensions(buffer)

  // Resolve font family
  const resolvedFont = FONT_FAMILIES[gridFont]

  // Per-font font size scale (mirrors GridBufferRenderer)
  const FONT_SIZE_SCALE: Record<GridFont, number> = {
    bedstead: 0.72,
    petme128: 1.0,
    teletext50: 0.85,
    pressstart2p: 0.65,
  }

  // Calculate cell size to fit the widget dimensions
  const cellSize = useMemo(() => {
    if (width && height) {
      const cw = Math.floor(width / cols)
      const ch = Math.floor(height / rows)
      return Math.min(cw, ch, 24)  // cap at 24px
    }
    return 24  // default square cell size
  }, [width, height, cols, rows])

  const adjFontSize = cellSize * FONT_SIZE_SCALE[gridFont]

  const cells = useMemo(() => {
    const result: React.ReactNode[] = []

    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cell = buffer[y][x]
        const fgColor = getColor(paletteId, cell.fg)
        const bgColor = getColor(paletteId, cell.bg)
        const key = `gw-${y}-${x}`

        result.push(
          <span
            key={key}
            style={{
              display: 'inline-block',
              width: cellSize,
              height: cellSize,
              lineHeight: cellSize + 'px',
              textAlign: 'center',
              color: fgColor,
              backgroundColor: bgColor,
              fontWeight: cell.bold ? 'bold' : 'normal',
              fontSize: adjFontSize,
              overflow: 'hidden',
            }}
          >
            {cell.char}
          </span>
        )
      }
    }

    return result
  }, [buffer, paletteId, cellSize, cols, rows, adjFontSize, gridFont])

  return (
    <div className={className} style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${cols}, ${cellSize}px)`,
      gridTemplateRows: `repeat(${rows}, ${cellSize}px)`,
      width: width || cols * cellSize,
      height: height || rows * cellSize,
      lineHeight: 0,
      fontSize: 0,
      overflow: 'hidden',
      fontFamily: resolvedFont,
      ...style,
    }}>
      {cells}
    </div>
  )
}


/**
 * Create a GridBuffer from a plain text string for use with GridWidget.
 * Each line becomes a row, each character a cell.
 */
export function textToGridBuffer(text: string, cols?: number): GridBuffer {
  const lines = text.split('\n')
  const maxCols = cols ?? Math.max(...lines.map(l => l.length))
  const rows = lines.length

  const buffer: GridBuffer = []
  for (let y = 0; y < rows; y++) {
    const line = lines[y]
    const row = []
    for (let x = 0; x < maxCols; x++) {
      row.push({
        char: x < line.length ? line[x] : ' ',
        fg: 7,
        bg: 0,
        bold: false,
        flash: false,
        doubleHeight: false,
        doubleWidth: false,
      })
    }
    buffer.push(row)
  }
  return buffer
}
