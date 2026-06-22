/* ═══════════════════════════════════════════════════════════════════
   useTeletextPage — Shared hook for TeletextGrid and TeletextPanel
   ═══════════════════════════════════════════════════════════════════
   Extracts common logic:
     - Page store singleton
     - Page navigation (goToPage, pageInput, showNav)
     - Live polling from Snackbar (every 10s)
     - Feed polling (every 15s)
     - Feed ticker rotation (every 5s)
     - Auto-rotate through P500-P599 live feed pages
     - User inactivity detection (resume auto-rotate after 60s)
     - Container resize observer
     - Cell editor state
     - SVG bridge import
   ═══════════════════════════════════════════════════════════════════ */

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { useStore, CHAR_W, CHAR_H, BORDER_MODE_CONFIGS } from '../GridUIStore'
import { TeletextPageStore } from '../grid-algebra/TeletextPage'
import type { TeletextPage } from '../grid-algebra/TeletextPage'
import { resize } from '@udos/gridcore'
import type { PaletteId } from '../grid-algebra/ColourPalette'
import { useSvgBridge } from './useSvgBridge'

// ─── Page Store Singleton ────────────────────────────────────────────

const pageStore = new TeletextPageStore()

// ─── Feed Item Type ──────────────────────────────────────────────────

export interface FeedItem {
  id: string
  source: string
  title: string
  body: string
  timestamp: string
  page: number
}

// ─── Cell Editor State ───────────────────────────────────────────────

export interface CellEditorState {
  row: number
  col: number
  char: string
  fg: number
  bg: number
  bold: boolean
  flash: boolean
}

// ─── Colour palettes for cell editor ─────────────────────────────────

export const FG_COLOURS = [
  { index: 0, label: 'Black', hex: '#0d1117' },
  { index: 1, label: 'Red', hex: '#da3633' },
  { index: 2, label: 'Green', hex: '#238636' },
  { index: 3, label: 'Yellow', hex: '#d29922' },
  { index: 4, label: 'Blue', hex: '#58a6ff' },
  { index: 5, label: 'Magenta', hex: '#bc8cff' },
  { index: 6, label: 'Cyan', hex: '#39d2c0' },
  { index: 7, label: 'White', hex: '#e6edf3' },
]

export const BG_COLOURS: { index: number; label: string; hex: string }[] = [
  { index: 0, label: 'Black', hex: '#0d1117' },
  { index: 1, label: 'Red', hex: '#da3633' },
  { index: 2, label: 'Green', hex: '#238636' },
  { index: 3, label: 'Yellow', hex: '#d29922' },
  { index: 4, label: 'Blue', hex: '#58a6ff' },
  { index: 5, label: 'Magenta', hex: '#bc8cff' },
  { index: 6, label: 'Cyan', hex: '#39d2c0' },
  { index: 7, label: 'White', hex: '#e6edf3' },
]

// ─── Hook Options ────────────────────────────────────────────────────

export interface UseTeletextPageOptions {
  initialPage?: number
  autoRotate?: boolean
  enableEditor?: boolean
  enableSvgImport?: boolean
  onPageChange?: (page: TeletextPage) => void
}

// ─── Hook Return Type ────────────────────────────────────────────────

export interface UseTeletextPageReturn {
  // Page state
  currentPage: TeletextPage
  setCurrentPage: (page: TeletextPage) => void
  pageStore: TeletextPageStore

  // Navigation
  pageInput: string
  showNav: boolean
  setShowNav: (v: boolean) => void
  inputRef: React.RefObject<HTMLInputElement | null>
  goToPage: (pageNum: number) => Promise<void>
  handlePageInput: (value: string) => void

  // Container sizing
  containerRef: React.RefObject<HTMLDivElement | null>
  containerSize: { w: number; h: number }

  // Live feed
  liveConnected: boolean
  feedItems: FeedItem[]
  feedIndex: number
  lastPollTime: number

  // Auto-rotate
  autoRotate: boolean
  userInteracted: boolean
  pauseAutoRotate: () => void

  // Cell editor
  editorMode: boolean
  setEditorMode: (v: boolean) => void
  cellEditor: CellEditorState | null
  setCellEditor: (v: CellEditorState | null) => void
  cellEditorRef: React.RefObject<HTMLDivElement | null>
  handleCellClick: (row: number, col: number) => void
  applyCellEdit: (updates: Partial<CellEditorState>) => void

  // SVG bridge
  svgBridge: ReturnType<typeof useSvgBridge>
  showSvgImport: boolean
  setShowSvgImport: (v: boolean) => void
  svgInput: string
  setSvgInput: (v: string) => void
  svgImportResult: string | null
  handleSvgImport: () => Promise<void>

  // Computed values
  paletteId: PaletteId
  displayBuffer: ReturnType<typeof resize>
  scale: number
  scaledCellW: number
  scaledCellH: number
  zoomedW: number
  zoomedH: number
  displayModeFilter: React.CSSProperties
  currentFeedItem: FeedItem | null
  pollTimeStr: string
  isLiveFeedPage: boolean
}

// ─── Hook ────────────────────────────────────────────────────────────

export function useTeletextPage(options: UseTeletextPageOptions = {}): UseTeletextPageReturn {
  const {
    initialPage = 100,
    autoRotate: enableAutoRotate = true,
    enableEditor = false,
    enableSvgImport = false,
    onPageChange,
  } = options

  const store = useStore()
  const [currentPage, setCurrentPage] = useState<TeletextPage>(pageStore.get(initialPage)!)
  const [pageInput, setPageInput] = useState('')
  const [showNav, setShowNav] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
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
  const LIVE_FEED_PAGES = useMemo(() =>
    Array.from({ length: 100 }, (_, i) => 500 + i), [])

  const [autoRotate, setAutoRotate] = useState(enableAutoRotate)
  const [autoRotateIndex, setAutoRotateIndex] = useState(0)
  const [userInteracted, setUserInteracted] = useState(false)
  const autoRotateTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const userInactivityRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const ROTATE_INTERVAL_MS = 15_000
  const USER_INACTIVITY_RESUME_MS = 60_000

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
        const pageNum = currentPage.meta.pageNumber
        const resp = await fetch(`http://127.0.0.1:8484/api/ceefax/page/${pageNum}`)
        if (!resp.ok) {
          setLiveConnected(false)
          return
        }
        const fetched = await pageStore.fetchFromSnackbar(pageNum)
        if (fetched && active) {
          setCurrentPage(fetched)
          setLiveConnected(true)
          setLastPollTime(Date.now())
          onPageChange?.(fetched)
        }
      } catch {
        if (active) setLiveConnected(false)
      }
    }
    poll()
    const interval = setInterval(poll, 10_000)
    return () => { active = false; clearInterval(interval) }
  }, [currentPage.meta.pageNumber, onPageChange])

  // ─── Poll feed items every 15s ────────────────────────────────────
  useEffect(() => {
    let active = true
    const pollFeed = async () => {
      try {
        const resp = await fetch('http://127.0.0.1:8484/api/ceefax/feed/latest?limit=20')
        if (!resp.ok) return
        const data = await resp.json()
        const items: FeedItem[] = data.items || []
        if (items.length > 0 && active) setFeedItems(items)
      } catch { /* keep existing */ }
    }
    pollFeed()
    const interval = setInterval(pollFeed, 15_000)
    return () => { active = false; clearInterval(interval) }
  }, [])

  // ─── Rotate feed ticker every 5s ──────────────────────────────────
  useEffect(() => {
    if (feedItems.length === 0) return
    feedTimerRef.current = setInterval(() => {
      setFeedIndex(prev => (prev + 1) % feedItems.length)
    }, 5_000)
    return () => { if (feedTimerRef.current) clearInterval(feedTimerRef.current) }
  }, [feedItems.length])

  // ─── Auto-rotate through P500-P599 ────────────────────────────────
  useEffect(() => {
    if (!autoRotate || userInteracted) return
    autoRotateTimerRef.current = setInterval(async () => {
      setAutoRotateIndex(prev => {
        const next = (prev + 1) % LIVE_FEED_PAGES.length
        const pageNum = LIVE_FEED_PAGES[next]
        pageStore.fetchFromSnackbar(pageNum).then(fetched => {
          if (fetched) {
            setCurrentPage(fetched)
            setLiveConnected(true)
            setLastPollTime(Date.now())
            onPageChange?.(fetched)
          }
        })
        return next
      })
    }, ROTATE_INTERVAL_MS)
    return () => { if (autoRotateTimerRef.current) clearInterval(autoRotateTimerRef.current) }
  }, [autoRotate, userInteracted, LIVE_FEED_PAGES, onPageChange])

  // ─── Pause auto-rotate on user interaction ────────────────────────
  const pauseAutoRotate = useCallback(() => {
    setUserInteracted(true)
    setAutoRotate(false)
    if (userInactivityRef.current) clearTimeout(userInactivityRef.current)
    userInactivityRef.current = setTimeout(() => {
      setAutoRotate(true)
      setUserInteracted(false)
    }, USER_INACTIVITY_RESUME_MS)
  }, [USER_INACTIVITY_RESUME_MS])

  useEffect(() => {
    return () => { if (userInactivityRef.current) clearTimeout(userInactivityRef.current) }
  }, [])

  // ─── Navigate to a page ───────────────────────────────────────────
  const goToPage = useCallback(async (pageNum: number) => {
    pauseAutoRotate()
    const fetched = await pageStore.fetchFromSnackbar(pageNum)
    if (fetched) {
      setCurrentPage(fetched)
      setLiveConnected(true)
      onPageChange?.(fetched)
    } else {
      const local = pageStore.get(pageNum)
      if (local) {
        setCurrentPage(local)
        setLiveConnected(false)
        onPageChange?.(local)
      }
    }
    setPageInput('')
    setShowNav(false)
  }, [pauseAutoRotate, onPageChange])

  // ─── Handle page input ────────────────────────────────────────────
  const handlePageInput = useCallback((value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 3)
    setPageInput(digits)
    if (digits.length === 3) goToPage(parseInt(digits, 10))
  }, [goToPage])

  // ─── Close cell editor on outside click ───────────────────────────
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (cellEditorRef.current && !cellEditorRef.current.contains(e.target as Node)) {
        setCellEditor(null)
      }
    }
    if (cellEditor) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [cellEditor])

  // ─── Unified palette ──────────────────────────────────────────────
  const paletteId: PaletteId = 'unified'

  // ─── Resize page buffer to viewport ───────────────────────────────
  const vp = store.viewport
  const displayBuffer = useMemo(() => {
    return resize(currentPage.buffer, vp.cols, vp.rows)
  }, [currentPage, vp.cols, vp.rows])

  // ─── Auto-zoom ────────────────────────────────────────────────────
  const cellW = CHAR_W
  const cellH = CHAR_H
  const contentW = vp.cols * cellW
  const contentH = vp.rows * cellH
  const borderCfg = BORDER_MODE_CONFIGS[vp.borderMode]
  const borderPadFraction = (1 - borderCfg.fillFraction) / 2
  const availableW = containerSize.w * (1 - borderPadFraction * 2)
  const availableH = containerSize.h * (1 - borderPadFraction * 2)
  const scaleX = availableW / contentW
  const scaleY = availableH / contentH
  const scale = Math.min(scaleX, scaleY, 4)
  const scaledCellW = cellW * scale
  const scaledCellH = cellH * scale
  const zoomedW = contentW * scale
  const zoomedH = contentH * scale

  const displayModeFilter: React.CSSProperties =
    store.displayMode === 'mono' ? { filter: 'grayscale(100%)' } :
    store.displayMode === 'wireframe' ? { filter: 'invert(100%) contrast(200%)' } :
    { filter: 'none' }

  // ─── Current feed item ────────────────────────────────────────────
  const currentFeedItem = feedItems.length > 0 ? feedItems[feedIndex % feedItems.length] : null
  const pollTimeStr = lastPollTime > 0
    ? new Date(lastPollTime).toLocaleTimeString()
    : '--:--:--'
  const isLiveFeedPage = currentPage.meta.pageNumber >= 500 && currentPage.meta.pageNumber <= 599

  // ─── Handle cell click in editor mode ─────────────────────────────
  const handleCellClick = useCallback((row: number, col: number) => {
    if (!editorMode) return
    const cell = displayBuffer[row]?.[col]
    if (!cell) return
    setCellEditor({ row, col, char: cell.char, fg: cell.fg, bg: cell.bg, bold: cell.bold, flash: cell.flash })
  }, [editorMode, displayBuffer])

  // ─── SVG Bridge ──────────────────────────────────────────────────
  const svgBridge = useSvgBridge()
  const [showSvgImport, setShowSvgImport] = useState(false)
  const [svgInput, setSvgInput] = useState('')
  const [svgImportResult, setSvgImportResult] = useState<string | null>(null)

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
    const lines = result.output.trim().split('\n')
    const buf = currentPage.buffer.map(r => r.map(c => ({ ...c })))
    for (let row = 0; row < Math.min(lines.length, buf.length); row++) {
      const line = lines[row].trim()
      if (!line || line.startsWith('#')) continue
      const cells = line.split(',')
      for (let col = 0; col < Math.min(cells.length, buf[row].length); col++) {
        const parts = cells[col].trim().split(':')
        if (parts.length >= 3) {
          buf[row][col] = {
            char: parts[0] === ' ' ? ' ' : parts[0],
            fg: parseInt(parts[1], 10) || 7,
            bg: parseInt(parts[2], 10) || 0,
            bold: false, flash: false, doubleHeight: false, doubleWidth: false,
          }
        }
      }
    }
    const updatedPage: TeletextPage = { ...currentPage, buffer: buf }
    pageStore.set(currentPage.meta.pageNumber, updatedPage)
    setCurrentPage(updatedPage)
    setSvgImportResult(`OK: Imported ${lines.length} rows from SVG`)
    setShowSvgImport(false)
    setSvgInput('')
    setTimeout(() => setSvgImportResult(null), 3000)
  }, [svgInput, svgBridge, currentPage])

  // ─── Apply cell edit ──────────────────────────────────────────────
  const applyCellEdit = useCallback((updates: Partial<CellEditorState>) => {
    if (!cellEditor) return
    const { row, col } = cellEditor
    const newChar = updates.char ?? cellEditor.char
    const newFg = updates.fg ?? cellEditor.fg
    const newBg = updates.bg ?? cellEditor.bg
    const newBold = updates.bold ?? cellEditor.bold
    const newFlash = updates.flash ?? cellEditor.flash
    const buf = currentPage.buffer.map(r => r.map(c => ({ ...c })))
    if (buf[row] && buf[row][col]) {
      buf[row][col] = { char: newChar, fg: newFg, bg: newBg, bold: newBold, flash: newFlash, doubleHeight: false, doubleWidth: false }
    }
    const updatedPage: TeletextPage = { ...currentPage, buffer: buf }
    pageStore.set(currentPage.meta.pageNumber, updatedPage)
    setCurrentPage(updatedPage)
    setCellEditor({ row, col, char: newChar, fg: newFg, bg: newBg, bold: newBold, flash: newFlash })
  }, [cellEditor, currentPage])

  return {
    currentPage,
    setCurrentPage,
    pageStore,
    pageInput,
    showNav,
    setShowNav,
    inputRef,
    goToPage,
    handlePageInput,
    containerRef,
    containerSize,
    liveConnected,
    feedItems,
    feedIndex,
    lastPollTime,
    autoRotate,
    userInteracted,
    pauseAutoRotate,
    editorMode,
    setEditorMode,
    cellEditor,
    setCellEditor,
    cellEditorRef,
    handleCellClick,
    applyCellEdit,
    svgBridge,
    showSvgImport,
    setShowSvgImport,
    svgInput,
    setSvgInput,
    svgImportResult,
    handleSvgImport,
    paletteId,
    displayBuffer,
    scale,
    scaledCellW,
    scaledCellH,
    zoomedW,
    zoomedH,
    displayModeFilter,
    currentFeedItem,
    pollTimeStr,
    isLiveFeedPage,
  }
}
