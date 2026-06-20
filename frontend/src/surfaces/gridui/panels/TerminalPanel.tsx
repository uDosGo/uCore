/* ═══════════════════════════════════════════════════════════════════
   TerminalPanel — BBC BASIC Terminal (BBCSDL-backed)
   ═══════════════════════════════════════════════════════════════════
   Uses GridBuffer internally for consistent rendering with
   TeletextPanel and GridWidget. All display operations go through
   GridTransform (resize, scroll) and ColourPalette (colour mapping).
   Viewport auto-zooms to fill available space with proper centering.
   
   Commands are sent to the BBCSDL bridge via the Snackbar API at
   POST /api/bbcsdl/exec for real BBC BASIC execution.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { useStore, CHAR_W, CHAR_H, BORDER_MODE_CONFIGS } from '../GridUIStore'
import { createBuffer, getDimensions } from '../grid-algebra/GridCell'
import type { GridBuffer } from '../grid-algebra/GridCell'
import { writeString } from '../grid-algebra/GridTransform'
import { GridBufferRenderer } from './GridBufferRenderer'
import { locationStore } from '../grid-algebra/LocationStore'
import { cityRegistry } from '../grid-algebra/CityRegistry'

// ─── Snackbar API URL ─────────────────────────────────────────────────
const SNACKBAR_URL = 'http://127.0.0.1:8484'

// ─── Terminal Line Buffer ────────────────────────────────────────────

interface TerminalLine {
  text: string
  fg?: number
  bg?: number
  bold?: boolean
}

// ─── Component ───────────────────────────────────────────────────────

export function TerminalPanel() {
  const store = useStore()
  const [lines, setLines] = useState<TerminalLine[]>([
    { text: '**** BBC BASIC (BBCSDL) ****', bold: true },
    { text: '' },
    { text: 'READY.', bold: true },
  ])
  const [inputBuffer, setInputBuffer] = useState('')
  const [lineNumber, setLineNumber] = useState(1)
  const [busy, setBusy] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const bodyRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerSize, setContainerSize] = useState({ w: 800, h: 600 })

  // ─── Measure container for auto-zoom ──────────────────────────────
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        const cs = entry.contentBoxSize?.[0]
        if (cs) {
          setContainerSize({ w: cs.inlineSize, h: cs.blockSize })
        } else {
          setContainerSize({ w: entry.contentRect.width, h: entry.contentRect.height })
        }
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const addLine = useCallback((text: string, bold = false) => {
    setLines(l => [...l, { text, bold }])
  }, [])

  // ─── Execute command via BBCSDL bridge ────────────────────────────
  const processCommand = useCallback(async (cmd: string) => {
    const upper = cmd.toUpperCase().trim()

    // Local commands (handled in-browser)
    if (upper === 'HELP' || upper === '?') {
      addLine('BBC BASIC Terminal — type any BBC BASIC command')
      addLine('Local commands: HELP, CLS, CLEAR, EXIT, QUIT')
      addLine('All other commands are sent to BBCSDL for real execution.')
      addLine('READY.', true)
      return
    }
    if (upper === 'CLS' || upper === 'CLEAR') {
      setLines([])
      addLine('READY.', true)
      return
    }
    if (upper === 'EXIT' || upper === 'QUIT') {
      addLine('GOODBYE.')
      return
    }

    // ─── Location commands ──────────────────────────────────────────
    if (upper === 'WHERE' || upper === 'LOCATION' || upper === 'LOC') {
      addLine(locationStore.getStatusString())
      addLine('READY.', true)
      return
    }

    if (upper === 'STATUS' || upper === 'STAT') {
      const loc = locationStore.getState()
      addLine(`Location: ${loc.locationName}`)
      addLine(`uCode: ${loc.uCode}`)
      addLine(`GPS: ${loc.lat.toFixed(4)}, ${loc.lon.toFixed(4)}`)
      addLine(`Zoom: L${loc.level} | Layer: ${loc.layer}`)
      addLine(`History: ${loc.history.length} locations`)
      addLine(`Bookmarks: ${loc.bookmarks.length}`)
      addLine('READY.', true)
      return
    }

    // GOTO <city> — jump to a city
    if (upper.startsWith('GOTO ') || upper.startsWith('GO ')) {
      const cityName = cmd.slice(upper.startsWith('GOTO ') ? 5 : 3).trim()
      if (!cityName) {
        addLine('?USAGE: GOTO <city name>')
        addLine('  Example: GOTO Tokyo')
        addLine('READY.', true)
        return
      }
      const result = locationStore.goToCity(cityName)
      addLine(result)
      addLine('READY.', true)
      return
    }

    // GPS <lat> <lon> — jump to coordinates
    if (upper.startsWith('GPS ')) {
      const parts = cmd.slice(4).trim().split(/\s+/)
      if (parts.length < 2) {
        addLine('?USAGE: GPS <latitude> <longitude>')
        addLine('  Example: GPS 35.6762 139.6503')
        addLine('READY.', true)
        return
      }
      const lat = parseFloat(parts[0])
      const lon = parseFloat(parts[1])
      if (isNaN(lat) || isNaN(lon)) {
        addLine('?INVALID COORDINATES')
        addLine('READY.', true)
        return
      }
      const result = locationStore.goToGPS(lat, lon)
      addLine(result)
      addLine('READY.', true)
      return
    }

    // UCODE <ucode> — jump to a uCode coordinate
    if (upper.startsWith('UCODE ')) {
      const uCode = cmd.slice(6).trim()
      if (!uCode) {
        addLine('?USAGE: UCODE <uCode>')
        addLine('  Example: UCODE L340-H42J-0K0K-0')
        addLine('READY.', true)
        return
      }
      const result = locationStore.goToUCode(uCode)
      addLine(result)
      addLine('READY.', true)
      return
    }

    // ZOOM IN / ZOOM OUT
    if (upper === 'ZOOM IN' || upper === 'ZOOM+') {
      const result = locationStore.zoomIn()
      addLine(result)
      addLine('READY.', true)
      return
    }
    if (upper === 'ZOOM OUT' || upper === 'ZOOM-') {
      const result = locationStore.zoomOut()
      addLine(result)
      addLine('READY.', true)
      return
    }

    // LEVEL <n> — set zoom level
    if (upper.startsWith('LEVEL ')) {
      const level = parseInt(cmd.slice(6).trim(), 10)
      if (isNaN(level) || level < 300 || level > 360) {
        addLine('?USAGE: LEVEL <300-360>')
        addLine('READY.', true)
        return
      }
      const result = locationStore.setLevel(level)
      addLine(result)
      addLine('READY.', true)
      return
    }

    // LAYER <n> — switch layer (0-5)
    if (upper.startsWith('LAYER ')) {
      const layer = parseInt(cmd.slice(6).trim(), 10)
      if (isNaN(layer) || layer < 0 || layer > 5) {
        addLine('?USAGE: LAYER <0-5>')
        addLine('READY.', true)
        return
      }
      const result = locationStore.setLayer(layer)
      addLine(result)
      addLine('READY.', true)
      return
    }

    // Directional movement: N, S, E, W, NE, NW, SE, SW
    if (/^(N|S|E|W|NE|NW|SE|SW)$/.test(upper)) {
      const result = locationStore.move(upper)
      addLine(result)
      addLine('READY.', true)
      return
    }

    // BOOKMARK — save current location
    if (upper === 'BOOKMARK' || upper === 'BM') {
      const result = locationStore.bookmarkCurrent()
      addLine(result)
      addLine('READY.', true)
      return
    }

    // BOOKMARKS — list bookmarks
    if (upper === 'BOOKMARKS' || upper === 'BMLIST') {
      const bookmarks = locationStore.getBookmarks()
      if (bookmarks.length === 0) {
        addLine('No bookmarks. Use BOOKMARK to save current location.')
      } else {
        addLine(`Bookmarks (${bookmarks.length}):`)
        bookmarks.forEach((b, i) => {
          const city = cityRegistry.findByUCode(b)
          addLine(`  ${i + 1}. ${city?.name || 'Unknown'} — ${b}`)
        })
      }
      addLine('READY.', true)
      return
    }

    // CITIES — list all cities
    if (upper === 'CITIES' || upper === 'CITYLIST') {
      const regions = cityRegistry.getRegions()
      addLine(`World Cities (${cityRegistry.count} total):`)
      regions.forEach(region => {
        const cities = cityRegistry.getByRegion(region)
        addLine(`  ${region}: ${cities.map(c => c.name).join(', ')}`)
      })
      addLine('READY.', true)
      return
    }

    // CITIES <region> — list cities in a region
    if (upper.startsWith('CITIES ') || upper.startsWith('REGION ')) {
      const regionName = cmd.slice(upper.startsWith('CITIES ') ? 7 : 7).trim().toLowerCase()
      const regionKey = regionName.replace(/\s+/g, '_')
      const cities = cityRegistry.getByRegion(regionKey)
      if (cities.length === 0) {
        addLine(`?REGION NOT FOUND: ${regionName}`)
        addLine('  Available: oceania, southeast_asia, east_asia, south_asia,')
        addLine('  europe, north_america, south_america, africa, middle_east')
      } else {
        addLine(`${regionName} (${cities.length} cities):`)
        cities.forEach(c => {
          addLine(`  ${c.name} — ${c.uCode} — P${c.teletextPage}`)
        })
      }
      addLine('READY.', true)
      return
    }

    // HISTORY — show location history
    if (upper === 'HISTORY') {
      const history = locationStore.getHistory()
      if (history.length === 0) {
        addLine('No history.')
      } else {
        addLine(`Location history (${history.length}):`)
        history.slice(-10).reverse().forEach((h, i) => {
          const city = cityRegistry.findByUCode(h)
          addLine(`  ${i + 1}. ${city?.name || 'Unknown'} — ${h}`)
        })
      }
      addLine('READY.', true)
      return
    }

    // Send to BBCSDL bridge via Snackbar API
    setBusy(true)
    try {
      const resp = await fetch(`${SNACKBAR_URL}/api/bbcsdl/exec`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd }),
      })
      const data = await resp.json()
      
      if (data.error) {
        addLine(`?ERROR: ${data.error}`)
      } else {
        // Show stdout lines
        if (data.stdout) {
          const stdoutLines = data.stdout.split('\n').filter((l: string) => l.trim())
          for (const line of stdoutLines) {
            addLine(line)
          }
        }
        // Show stderr if any
        if (data.stderr) {
          const stderrLines = data.stderr.split('\n').filter((l: string) => l.trim())
          for (const line of stderrLines) {
            addLine(`?${line}`, true)
          }
        }
        // Show error on non-zero return
        if (data.returncode && data.returncode !== 0 && !data.stdout && !data.stderr) {
          addLine(`?ERROR: exit code ${data.returncode}`)
        }
      }
    } catch (err) {
      addLine(`?ERROR: Cannot reach BBCSDL bridge (${err instanceof Error ? err.message : 'connection failed'})`)
      addLine('  Is the Snackbar server running on port 8484?')
    }
    setBusy(false)
    addLine('READY.', true)
  }, [addLine])

  const handleInput = useCallback(() => {
    const cmd = inputBuffer.trim()
    if (!cmd) return
    addLine(cmd)
    processCommand(cmd)
    setInputBuffer('')
    setLineNumber(n => n + 1)
    setTimeout(() => { bodyRef.current?.scrollTo(0, bodyRef.current.scrollHeight); inputRef.current?.focus() }, 0)
  }, [inputBuffer, addLine, processCommand])

  useEffect(() => { inputRef.current?.focus() }, [])

  // ─── Build GridBuffer from lines ──────────────────────────────────
  const vp = store.viewport
  const gridBuffer = useMemo<GridBuffer>(() => {
    const cols = vp.cols
    const rows = vp.rows
    let buf = createBuffer(cols, rows)

    let y = 0
    for (const line of lines) {
      if (y >= rows) break
      buf = writeString(buf, 0, y, line.text, line.fg ?? 7, line.bg ?? 0, line.bold ?? false)
      y++
    }

    if (y < rows) {
      const prompt = `${lineNumber} `
      buf = writeString(buf, 0, y, prompt + inputBuffer, 7, 0, true)
    }

    return buf
  }, [lines, inputBuffer, lineNumber, vp.cols, vp.rows])

  // ─── Auto-zoom: calculate scale to fit container ──────────────────
  const cellW = CHAR_W
  const cellH = CHAR_H
  const contentW = vp.cols * cellW
  const contentH = vp.rows * cellH

  // Border padding: the border takes up (1 - fillFraction) of the space
  const borderCfg = BORDER_MODE_CONFIGS[vp.borderMode]
  const borderPadFraction = (1 - borderCfg.fillFraction) / 2

  // Available space after border padding
  const availableW = containerSize.w * (1 - borderPadFraction * 2)
  const availableH = containerSize.h * (1 - borderPadFraction * 2)

  const scaleX = availableW / contentW
  const scaleY = availableH / contentH
  const scale = Math.min(scaleX, scaleY, 4)
  // Render cells at their final scaled size so fonts are crisp (no blurry CSS scaling)
  const scaledCellW = cellW * scale
  const scaledCellH = cellH * scale
  const zoomedW = contentW * scale
  const zoomedH = contentH * scale

  const displayModeFilter: React.CSSProperties =
    store.displayMode === 'mono' ? { filter: 'grayscale(100%)' } :
    store.displayMode === 'wireframe' ? { filter: 'invert(100%) contrast(200%)' } :
    { filter: 'none' }

  return (
    <div className="gridui-panel">
      {/* Viewport area: fills remaining space, applies border padding, centers the grid */}
      <div
        ref={containerRef}
        className="gridui-terminal-viewport"
        style={{
          padding: `${containerSize.h * borderPadFraction}px ${containerSize.w * borderPadFraction}px`,
        }}
      >
        <div
          ref={bodyRef}
          className="gridui-terminal-screen"
          style={{
            width: zoomedW,
            height: zoomedH,
            ...displayModeFilter,
          }}
        >
          <GridBufferRenderer
            buffer={gridBuffer}
            paletteId="unified"
            cellWidth={scaledCellW}
            cellHeight={scaledCellH}
            gridFont={store.gridFont}
          />
        </div>
      </div>
      {/* Hidden input for keyboard capture */}
      <input
        ref={inputRef}
        value={inputBuffer}
        onChange={e => setInputBuffer(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') handleInput() }}
        style={{ position: 'absolute', opacity: 0, height: 0, width: 0 }}
        aria-hidden="true"
      />
    </div>
  )
}
