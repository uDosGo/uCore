/* ═══════════════════════════════════════════════════════════════════
   TeletextPanel — Ceefex-style teletext page viewer
   ═══════════════════════════════════════════════════════════════════
   Uses grid-algebra for rendering. Pages are GridBuffers stored in
   TeletextPageStore. Navigation via 3-digit page number.
   Viewport auto-zooms to fill available space with proper centering.

   Features:
     - 3-digit page dialer (type a number to navigate)
     - Built-in pages: Welcome (100), System Status (101), News (200)
     - Colour Test Card (888)
     - Viewport presets: 28×28 (1:1), 48×36 (4:3), 64×36 (16:9)
     - Viewport resize via GridTransform
     - Live page polling from Snackbar API (every 10s)
     - Scrolling feed ticker at bottom of page
     - "LIVE" indicator when connected to Snackbar
     - Page Editor Mode: click any cell to edit its character/colour
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { useStore, CHAR_W, CHAR_H, BORDER_MODE_CONFIGS } from '../GridUIStore'
import { TeletextPageStore } from '../grid-algebra/TeletextPage'
import type { TeletextPage } from '../grid-algebra/TeletextPage'
import { resize } from '../grid-algebra/GridTransform'
import { GridBufferRenderer } from './GridBufferRenderer'
import type { PaletteId } from '../grid-algebra/ColourPalette'
import { getColor } from '../grid-algebra/ColourPalette'
import { useSvgBridge } from '../hooks/useSvgBridge'
import type { SvgConvertResult } from '../hooks/useSvgBridge'

// ─── Page Store Singleton ────────────────────────────────────────────

const pageStore = new TeletextPageStore()

// ─── Feed Item Type ──────────────────────────────────────────────────

interface FeedItem {
  id: string
  source: string
  title: string
  body: string
  timestamp: string
  page: number
}

// ─── Cell Editor Popup ───────────────────────────────────────────────

interface CellEditorState {
  row: number
  col: number
  char: string
  fg: number
  bg: number
  bold: boolean
  flash: boolean
}

const FG_COLOURS = [
  { index: 0, label: 'Black', hex: '#0d1117' },
  { index: 1, label: 'Red', hex: '#da3633' },
  { index: 2, label: 'Green', hex: '#238636' },
  { index: 3, label: 'Yellow', hex: '#d29922' },
  { index: 4, label: 'Blue', hex: '#58a6ff' },
  { index: 5, label: 'Magenta', hex: '#bc8cff' },
  { index: 6, label: 'Cyan', hex: '#39d2c0' },
  { index: 7, label: 'White', hex: '#e6edf3' },
]

const BG_COLOURS = [
  { index: 0, label: 'Black', hex: '#0d1117' },
  { index: 1, label: 'Red', hex: '#da3633' },
  { index: 2, label: 'Green', hex: '#238636' },
  { index: 3, label: 'Yellow', hex: '#d29922' },
  { index: 4, label: 'Blue', hex: '#58a6ff' },
  { index: 5, label: 'Magenta', hex: '#bc8cff' },
  { index: 6, label: 'Cyan', hex: '#39d2c0' },
  { index: 7, label: 'White', hex: '#e6edf3' },
]

// ─── Teletext Panel ──────────────────────────────────────────────────

export function TeletextPanel() {
  const store = useStore()
  const [currentPage, setCurrentPage] = useState<TeletextPage>(pageStore.get(100)!)
  const [pageInput, setPageInput] = useState('')
  const [showNav, setShowNav] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const bodyRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerSize, setContainerSize] = useState({ w: 800, h: 600 })

  // ─── Page Editor Mode ─────────────────────────────────────────────
  const [editorMode, setEditorMode] = useState(false)
  const [cellEditor, setCellEditor] = useState<CellEditorState | null>(null)
  const cellEditorRef = useRef<HTMLDivElement>(null)

  // ─── Live feed state ──────────────────────────────────────────────
  const [liveConnected, setLiveConnected] = useState(false)
  const [feedItems, setFeedItems] = useState<FeedItem[]>([])
  const [feedIndex, setFeedIndex] = useState(0)
  const [lastPollTime, setLastPollTime] = useState<number>(0)
  const feedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // ─── Auto-rotate through P500-P599 live feed pages ────────────────
  const LIVE_FEED_PAGES = [500, 501, 502, 503, 504, 505, 506, 507, 508, 509,
                            510, 511, 512, 513, 514, 515, 516, 517, 518, 519,
                            520, 521, 522, 523, 524, 525, 526, 527, 528, 529,
                            530, 531, 532, 533, 534, 535, 536, 537, 538, 539,
                            540, 541, 542, 543, 544, 545, 546, 547, 548, 549,
                            550, 551, 552, 553, 554, 555, 556, 557, 558, 559,
                            560, 561, 562, 563, 564, 565, 566, 567, 568, 569,
                            570, 571, 572, 573, 574, 575, 576, 577, 578, 579,
                            580, 581, 582, 583, 584, 585, 586, 587, 588, 589,
                            590, 591, 592, 593, 594, 595, 596, 597, 598, 599]

  // ─── BBCSDL P700-P799 auto-rotate ──────────────────────────────────
  const BBCSDL_PAGES = [700, 701, 702, 703, 704, 705, 706, 707, 708, 709,
                         710, 711, 712, 713, 714, 715, 716, 717, 718, 719,
                         720, 721, 722, 723, 724, 725, 726, 727, 728, 729,
                         730, 731, 732, 733, 734, 735, 736, 737, 738, 739,
                         740, 741, 742, 743, 744, 745, 746, 747, 748, 749,
                         750, 751, 752, 753, 754, 755, 756, 757, 758, 759,
                         760, 761, 762, 763, 764, 765, 766, 767, 768, 769,
                         770, 771, 772, 773, 774, 775, 776, 777, 778, 779,
                         780, 781, 782, 783, 784, 785, 786, 787, 788, 789,
                         790, 791, 792, 793, 794, 795, 796, 797, 798, 799]
  const [bbcsdlConnected, setBbcsdlConnected] = useState(false)
  const [bbcsdlRotate, setBbcsdlRotate] = useState(true)
  const [bbcsdlRotateIndex, setBbcsdlRotateIndex] = useState(0)
  const bbcsdlTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const BBCSDL_ROTATE_INTERVAL_MS = 10_000  // 10 seconds per BBCSDL page

  const [autoRotate, setAutoRotate] = useState(true)
  const [autoRotateIndex, setAutoRotateIndex] = useState(0)
  const [userInteracted, setUserInteracted] = useState(false)
  const autoRotateTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const userInactivityRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const ROTATE_INTERVAL_MS = 15_000  // 15 seconds per page
  const USER_INACTIVITY_RESUME_MS = 60_000  // Resume auto-rotate after 60s of inactivity


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

  // ─── Poll live pages from Snackbar every 10s ──────────────────────
  useEffect(() => {
    let active = true

    const poll = async () => {
      try {
        // Try fetching the current page from Snackbar
        const pageNum = currentPage.meta.pageNumber
        const resp = await fetch(`http://127.0.0.1:8484/v1/ceefax/page/${pageNum}`)
        if (!resp.ok) {
          setLiveConnected(false)
          return
        }
        const data = await resp.json()
        if (!data.page) {
          setLiveConnected(false)
          return
        }

        // Fetch the page into the store (reuses existing fetchFromSnackbar logic)
        const fetched = await pageStore.fetchFromSnackbar(pageNum)
        if (fetched && active) {
          setCurrentPage(fetched)
          setLiveConnected(true)
          setLastPollTime(Date.now())
        }
      } catch {
        // Snackbar not available — stay offline
        if (active) setLiveConnected(false)
      }
    }

    // Initial poll
    poll()

    const interval = setInterval(poll, 10_000)
    return () => {
      active = false
      clearInterval(interval)
    }
  }, [currentPage.meta.pageNumber])

  // ─── Poll feed items every 15s ────────────────────────────────────
  useEffect(() => {
    let active = true

    const pollFeed = async () => {
      try {
        const resp = await fetch('http://127.0.0.1:8484/v1/ceefax/feed/latest?limit=20')
        if (!resp.ok) return
        const data = await resp.json()
        const items: FeedItem[] = data.items || []
        if (items.length > 0 && active) {
          setFeedItems(items)
        }
      } catch {
        // Feed unavailable — keep existing items
      }
    }

    pollFeed()
    const interval = setInterval(pollFeed, 15_000)
    return () => {
      active = false
      clearInterval(interval)
    }
  }, [])

  // ─── Rotate feed ticker every 5s ──────────────────────────────────
  useEffect(() => {
    if (feedItems.length === 0) return

    feedTimerRef.current = setInterval(() => {
      setFeedIndex(prev => (prev + 1) % feedItems.length)
    }, 5_000)

    return () => {
      if (feedTimerRef.current) clearInterval(feedTimerRef.current)
    }
  }, [feedItems.length])

  // ─── Auto-rotate through P500-P599 live feed pages ────────────────
  useEffect(() => {
    if (!autoRotate || userInteracted) return

    autoRotateTimerRef.current = setInterval(async () => {
      setAutoRotateIndex(prev => {
        const next = (prev + 1) % LIVE_FEED_PAGES.length
        const pageNum = LIVE_FEED_PAGES[next]
        // Fetch the next live feed page from Snackbar
        pageStore.fetchFromSnackbar(pageNum).then(fetched => {
          if (fetched) {
            setCurrentPage(fetched)
            setLiveConnected(true)
            setLastPollTime(Date.now())
          }
        })
        return next
      })
    }, ROTATE_INTERVAL_MS)

    return () => {
      if (autoRotateTimerRef.current) clearInterval(autoRotateTimerRef.current)
    }
  }, [autoRotate, userInteracted, LIVE_FEED_PAGES.length])

  // ─── BBCSDL P700-P799 auto-rotate ────────────────────────────────────
  useEffect(() => {
    if (!bbcsdlRotate) return

    bbcsdlTimerRef.current = setInterval(async () => {
      setBbcsdlRotateIndex(prev => {
        const next = (prev + 1) % BBCSDL_PAGES.length
        const pageNum = BBCSDL_PAGES[next]
        // Fetch the next BBCSDL page from Snackbar
        pageStore.fetchFromSnackbar(pageNum).then(fetched => {
          if (fetched) {
            setCurrentPage(fetched)
            setBbcsdlConnected(true)
            setLastPollTime(Date.now())
          }
        })
        return next
      })
    }, BBCSDL_ROTATE_INTERVAL_MS)

    return () => {
      if (bbcsdlTimerRef.current) clearInterval(bbcsdlTimerRef.current)
    }
  }, [bbcsdlRotate, BBCSDL_PAGES.length])

  // ─── Pause auto-rotate on user interaction, resume after inactivity ──
  const pauseAutoRotate = useCallback(() => {
    setUserInteracted(true)
    setAutoRotate(false)
    // Clear any existing inactivity timer
    if (userInactivityRef.current) clearTimeout(userInactivityRef.current)
    // Set a timer to resume auto-rotate after inactivity
    userInactivityRef.current = setTimeout(() => {
      setAutoRotate(true)
      setUserInteracted(false)
    }, USER_INACTIVITY_RESUME_MS)
  }, [USER_INACTIVITY_RESUME_MS])

  // Cleanup inactivity timer on unmount
  useEffect(() => {
    return () => {
      if (userInactivityRef.current) clearTimeout(userInactivityRef.current)
    }
  }, [])


  // Navigate to a page (try Snackbar first, fall back to local)
  const goToPage = useCallback(async (pageNum: number) => {
    // Pause auto-rotate when user manually navigates
    pauseAutoRotate()
    // Try fetching from Snackbar first
    const fetched = await pageStore.fetchFromSnackbar(pageNum)
    if (fetched) {
      setCurrentPage(fetched)
      setLiveConnected(true)
    } else {
      // Fall back to local built-in page
      const local = pageStore.get(pageNum)
      if (local) {
        setCurrentPage(local)
        setLiveConnected(false)
      }
    }
    setPageInput('')
    setShowNav(false)
  }, [pauseAutoRotate])


  // Handle page input
  const handlePageInput = useCallback((value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 3)
    setPageInput(digits)
    if (digits.length === 3) {
      goToPage(parseInt(digits, 10))
    }
  }, [goToPage])

  // Keyboard shortcut: focus page input
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (/^[0-9]$/.test(e.key) && document.activeElement !== inputRef.current) {
        setShowNav(true)
        setTimeout(() => inputRef.current?.focus(), 0)
      }
      if (e.key === 'Escape') {
        setShowNav(false)
        setPageInput('')
        setCellEditor(null)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // ─── Close cell editor on outside click ───────────────────────────
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (cellEditorRef.current && !cellEditorRef.current.contains(e.target as Node)) {
        setCellEditor(null)
      }
    }
    if (cellEditor) {
      document.addEventListener('mousedown', handleClick)
    }
    return () => document.removeEventListener('mousedown', handleClick)
  }, [cellEditor])

  // ─── Unified palette (always 'unified') ───────────────────────────
  const paletteId: PaletteId = 'unified'

  // ─── Resize page buffer to viewport ───────────────────────────────
  const vp = store.viewport
  const displayBuffer = useMemo(() => {
    return resize(currentPage.buffer, vp.cols, vp.rows)
  }, [currentPage, vp.cols, vp.rows])

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

  // ─── Current feed item for ticker ─────────────────────────────────
  const currentFeedItem = feedItems.length > 0 ? feedItems[feedIndex % feedItems.length] : null

  // ─── Format last poll time ────────────────────────────────────────
  const pollTimeStr = lastPollTime > 0
    ? new Date(lastPollTime).toLocaleTimeString()
    : '--:--:--'

  // ─── Check if current page is in the live feed range ──────────────
  const isLiveFeedPage = currentPage.meta.pageNumber >= 500 && currentPage.meta.pageNumber <= 599

  // ─── Handle cell click in editor mode ─────────────────────────────
  const handleCellClick = useCallback((row: number, col: number) => {
    if (!editorMode) return
    const cell = displayBuffer[row]?.[col]
    if (!cell) return
    setCellEditor({
      row,
      col,
      char: cell.char,
      fg: cell.fg,
      bg: cell.bg,
      bold: cell.bold,
      flash: cell.flash,
    })
  }, [editorMode, displayBuffer])

  // ─── SVG Bridge ──────────────────────────────────────────────────
  const svgBridge = useSvgBridge()
  const [showSvgImport, setShowSvgImport] = useState(false)
  const [svgInput, setSvgInput] = useState('')
  const [svgImportResult, setSvgImportResult] = useState<string | null>(null)
  const svgTextareaRef = useRef<HTMLTextAreaElement>(null)

  // ─── Import SVG as teletext block graphics ────────────────────────
  const handleSvgImport = useCallback(async () => {
    if (!svgInput.trim()) return
    setSvgImportResult(null)
    const result = await svgBridge.convert(svgInput, 'celx')
    if (!result) {
      setSvgImportResult('?SVG import failed — is Snackbar running?')
      return
    }
    if (result.error) {
      setSvgImportResult(`?${result.error}`)
      return
    }

    // Parse CELX output into the current page buffer
    // CELX format: rows of comma-separated "char:fg:bg" tokens
    const lines = result.output.trim().split('\n')
    const buf = currentPage.buffer.map(r => r.map(c => ({ ...c })))
    for (let row = 0; row < Math.min(lines.length, buf.length); row++) {
      const line = lines[row].trim()
      if (!line || line.startsWith('#')) continue
      const cells = line.split(',')
      for (let col = 0; col < Math.min(cells.length, buf[row].length); col++) {
        const parts = cells[col].trim().split(':')
        if (parts.length >= 3) {
          const char = parts[0] === ' ' ? ' ' : parts[0]
          const fg = parseInt(parts[1], 10) || 7
          const bg = parseInt(parts[2], 10) || 0
          buf[row][col] = {
            char,
            fg,
            bg,
            bold: false,
            flash: false,
            doubleHeight: false,
            doubleWidth: false,
          }
        }
      }
    }

    const updatedPage: TeletextPage = {
      ...currentPage,
      buffer: buf,
    }
    pageStore.set(currentPage.meta.pageNumber, updatedPage)
    setCurrentPage(updatedPage)
    setSvgImportResult(`OK: Imported ${lines.length} rows from SVG`)
    setShowSvgImport(false)
    setSvgInput('')
    setTimeout(() => setSvgImportResult(null), 3000)
  }, [svgInput, svgBridge, currentPage])

  // ─── Apply cell edit to the page buffer ───────────────────────────
  const applyCellEdit = useCallback((updates: Partial<CellEditorState>) => {
    if (!cellEditor) return
    const { row, col } = cellEditor
    const newChar = updates.char ?? cellEditor.char
    const newFg = updates.fg ?? cellEditor.fg
    const newBg = updates.bg ?? cellEditor.bg
    const newBold = updates.bold ?? cellEditor.bold
    const newFlash = updates.flash ?? cellEditor.flash

    // Clone the page buffer and update the cell
    const buf = currentPage.buffer.map(r => r.map(c => ({ ...c })))
    if (buf[row] && buf[row][col]) {
      buf[row][col] = {
        char: newChar,
        fg: newFg,
        bg: newBg,
        bold: newBold,
        flash: newFlash,
        doubleHeight: false,
        doubleWidth: false,
      }
    }

    // Create updated page
    const updatedPage: TeletextPage = {
      ...currentPage,
      buffer: buf,
    }
    pageStore.set(currentPage.meta.pageNumber, updatedPage)
    setCurrentPage(updatedPage)
    setCellEditor({
      row,
      col,
      char: newChar,
      fg: newFg,
      bg: newBg,
      bold: newBold,
      flash: newFlash,
    })
  }, [cellEditor, currentPage])

  return (
    <div className="gridui-panel">
      {/* Viewport area: fills remaining space, applies border padding, centers the grid */}
      <div
        ref={containerRef}
        className="gridui-terminal-viewport"
        style={{
          padding: `${containerSize.h * borderPadFraction}px ${containerSize.w * borderPadFraction}px`,
          cursor: editorMode ? 'cell' : 'default',
        }}
      >
        <div
          ref={bodyRef}
          className="gridui-terminal-screen"
          style={{
            width: zoomedW,
            height: zoomedH,
            ...displayModeFilter,
            position: 'relative',
          }}
        >
          {/* Click overlay for editor mode */}
          {editorMode && (
            <div style={{ position: 'absolute', inset: 0, zIndex: 10 }}>
              {Array.from({ length: vp.rows }).map((_, row) => (
                <div key={row} style={{ display: 'flex', height: scaledCellH }}>
                  {Array.from({ length: vp.cols }).map((_, col) => (
                    <div
                      key={col}
                      onClick={() => handleCellClick(row, col)}
                      style={{
                        width: scaledCellW,
                        height: scaledCellH,
                        cursor: 'pointer',
                      }}
                      title={`(${col}, ${row})`}
                    />
                  ))}
                </div>
              ))}
            </div>
          )}

          <GridBufferRenderer
            buffer={displayBuffer}
            paletteId={paletteId}
            cellWidth={scaledCellW}
            cellHeight={scaledCellH}
            gridFont={store.gridFont}
          />
        </div>
      </div>

      {/* Cell Editor Popup */}
      {cellEditor && (
        <div
          ref={cellEditorRef}
          className="gridui-cell-editor-popup"
          style={{
            position: 'absolute',
            bottom: 80,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 100,
            background: '#161b22',
            border: '1px solid #30363d',
            borderRadius: 8,
            padding: 12,
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            minWidth: 320,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ color: '#e6edf3', fontSize: 13, fontWeight: 600 }}>
              Cell ({cellEditor.col}, {cellEditor.row})
            </span>
            <button
              onClick={() => setCellEditor(null)}
              className="gridui-btn--close"
              style={{ marginLeft: 'auto', width: 20, height: 20, fontSize: 12 }}
            >
              ✕
            </button>
          </div>

          {/* Character input */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
            <label style={{ color: '#8b949e', fontSize: 12, minWidth: 60 }}>Character</label>
            <input
              value={cellEditor.char}
              onChange={e => applyCellEdit({ char: e.target.value.slice(0, 1) || ' ' })}
              maxLength={1}
              className="gridui-input"
              style={{ width: 40, textAlign: 'center', fontSize: 16 }}
            />
            <span style={{
              fontSize: 20,
              color: getColor(paletteId, cellEditor.fg),
              fontFamily: "'Bedstead','PetMe128',monospace",
              padding: '2px 8px',
              background: getColor(paletteId, cellEditor.bg),
              borderRadius: 4,
            }}>
              {cellEditor.char}
            </span>
          </div>

          {/* Foreground colour */}
          <div style={{ marginBottom: 8 }}>
            <label style={{ color: '#8b949e', fontSize: 12, display: 'block', marginBottom: 4 }}>Foreground</label>
            <div style={{ display: 'flex', gap: 4 }}>
              {FG_COLOURS.map(c => (
                <button
                  key={c.index}
                  onClick={() => applyCellEdit({ fg: c.index })}
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 4,
                    background: c.hex,
                    border: cellEditor.fg === c.index ? '2px solid #e6edf3' : '1px solid #30363d',
                    cursor: 'pointer',
                  }}
                  title={c.label}
                />
              ))}
            </div>
          </div>

          {/* Background colour */}
          <div style={{ marginBottom: 8 }}>
            <label style={{ color: '#8b949e', fontSize: 12, display: 'block', marginBottom: 4 }}>Background</label>
            <div style={{ display: 'flex', gap: 4 }}>
              {BG_COLOURS.map(c => (
                <button
                  key={c.index}
                  onClick={() => applyCellEdit({ bg: c.index })}
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 4,
                    background: c.hex,
                    border: cellEditor.bg === c.index ? '2px solid #e6edf3' : '1px solid #30363d',
                    cursor: 'pointer',
                  }}
                  title={c.label}
                />
              ))}
            </div>
          </div>

          {/* Bold / Flash toggles */}
          <div style={{ display: 'flex', gap: 12 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#e6edf3', fontSize: 12, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={cellEditor.bold}
                onChange={e => applyCellEdit({ bold: e.target.checked })}
                style={{ accentColor: '#58a6ff' }}
              />
              Bold
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#e6edf3', fontSize: 12, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={cellEditor.flash}
                onChange={e => applyCellEdit({ flash: e.target.checked })}
                style={{ accentColor: '#58a6ff' }}
              />
              Flash
            </label>
          </div>
        </div>
      )}

      {/* Page Navigation Overlay */}
      {showNav && (
        <div className="gridui-teletext-nav-overlay">
          <span className="gridui-teletext-nav-label">PAGE</span>
          <input
            ref={inputRef}
            value={pageInput}
            onChange={e => handlePageInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && pageInput.length > 0) {
                goToPage(parseInt(pageInput, 10))
              }
              if (e.key === 'Escape') {
                setShowNav(false)
                setPageInput('')
              }
            }}
            placeholder="---"
            maxLength={3}
            className="gridui-teletext-nav-input"
          />
          <button
            onClick={() => { setShowNav(false); setPageInput('') }}
            className="gridui-teletext-nav-close"
          >
            ✕
          </button>
        </div>
      )}

      {/* Page Info Bar */}
      <div className="gridui-teletext-info-bar">
        <span>P{currentPage.meta.pageNumber.toString().padStart(3, '0')}</span>
        <span>{currentPage.meta.title}</span>
        <span className="gridui-teletext-poll-time">@{pollTimeStr}</span>
        {liveConnected && (
          <span className="gridui-teletext-live-badge">LIVE</span>
        )}
        {isLiveFeedPage && autoRotate && (
          <span className="gridui-teletext-feed-badge">LIVE FEED</span>
        )}
        {isLiveFeedPage && !autoRotate && (
          <span className="gridui-teletext-feed-badge gridui-teletext-feed-badge-paused">FEED (PAUSED)</span>
        )}
        {bbcsdlConnected && (
          <span className="gridui-teletext-bbcsdl-badge">BBCSDL</span>
        )}
        <button
          onClick={() => setShowNav(v => !v)}
          className="gridui-teletext-goto-btn"
        >
          GO TO PAGE
        </button>
        <button
          onClick={() => { setEditorMode(v => !v); setCellEditor(null) }}
          className={`gridui-teletext-goto-btn ${editorMode ? 'gridui-teletext-goto-btn--active' : ''}`}
          style={{
            marginLeft: 4,
            background: editorMode ? '#238636' : undefined,
            color: editorMode ? '#fff' : undefined,
          }}
        >
          {editorMode ? 'EDITING' : 'EDIT'}
        </button>
        <button
          onClick={() => setShowSvgImport(v => !v)}
          className="gridui-teletext-goto-btn"
          style={{ marginLeft: 4 }}
          title="Import SVG as teletext block graphics"
        >
          SVG
        </button>
      </div>

      {/* SVG Import Modal */}
      {showSvgImport && (
        <div style={{
          position: 'absolute',
          inset: 0,
          zIndex: 200,
          background: 'rgba(0,0,0,0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <div style={{
            background: '#161b22',
            border: '1px solid #30363d',
            borderRadius: 8,
            padding: 16,
            width: '80%',
            maxWidth: 600,
            maxHeight: '80%',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#e6edf3' }}>
                Import SVG as Teletext Block Graphics
              </h3>
              <button onClick={() => { setShowSvgImport(false); setSvgInput('') }} className="gridui-btn--close" style={{ width: 24, height: 24, fontSize: 14 }}>✕</button>
            </div>
            <p style={{ margin: 0, fontSize: 12, color: '#8b949e' }}>
              Paste SVG markup below. It will be converted to CELX format via the uVector SVG bridge
              and rendered as teletext block graphics on the current page.
            </p>
            <textarea
              ref={svgTextareaRef}
              value={svgInput}
              onChange={e => setSvgInput(e.target.value)}
              placeholder={`<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">\n  <rect x="10" y="10" width="80" height="80" fill="blue"/>\n</svg>`}
              style={{
                width: '100%',
                minHeight: 200,
                background: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: 4,
                color: '#e6edf3',
                fontSize: 12,
                fontFamily: "'SF Mono','Fira Code',monospace",
                padding: 8,
                resize: 'vertical',
              }}
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              {svgBridge.loading && (
                <span style={{ color: '#8b949e', fontSize: 12 }}>Converting…</span>
              )}
              <button
                onClick={() => { setShowSvgImport(false); setSvgInput('') }}
                className="gridui-btn"
                style={{ fontSize: 12, padding: '4px 12px' }}
              >
                Cancel
              </button>
              <button
                onClick={handleSvgImport}
                disabled={svgBridge.loading || !svgInput.trim()}
                className="gridui-btn gridui-btn--primary"
                style={{ fontSize: 12, padding: '4px 12px' }}
              >
                {svgBridge.loading ? 'Converting…' : 'Import'}
              </button>
            </div>
            {svgImportResult && (
              <div style={{
                padding: '6px 10px',
                borderRadius: 4,
                fontSize: 12,
                background: svgImportResult.startsWith('?') ? '#E76F5120' : '#23863620',
                border: `1px solid ${svgImportResult.startsWith('?') ? '#E76F5140' : '#3fb95040'}`,
                color: svgImportResult.startsWith('?') ? '#E76F51' : '#3fb950',
              }}>
                {svgImportResult}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scrolling Feed Ticker */}
      {currentFeedItem && (
        <div className="gridui-teletext-feed-ticker">
          <span className="gridui-teletext-ticker-source">{currentFeedItem.source}</span>
          <span className="gridui-teletext-ticker-title">{currentFeedItem.title}</span>
          <span className="gridui-teletext-ticker-body">{currentFeedItem.body}</span>
          <span className="gridui-teletext-ticker-time">{new Date(currentFeedItem.timestamp).toLocaleTimeString()}</span>
        </div>
      )}
    </div>
  )

}
