/* ═══════════════════════════════════════════════════════════════════
   TeletextPage — Teletext page store and page builder
   ═══════════════════════════════════════════════════════════════════
   A TeletextPage is a GridBuffer with page metadata.
   Built-in pages use the standard 48×36 (4:3) buffer size.
   The page store holds pages in memory, keyed by 3-digit page number.

   Page ranges:
     P100-P199 — Index/Welcome, System Status, Help, About
     P200-P299 — News, Dev Log, Changelog
     P300-P399 — Surface Status (uCode1, uServer, uConnect, etc.)
     P400-P499 — Weather, Time, Date
     P500-P599 — Live feed pages (email, RSS, GitHub, Slack)
     P600-P699 — Gallery/Design showcase (Ceefax in-vision style)
     P700-P799 — Reserved
     P800-P899 — Test cards, colour bars, diagnostics

   NOTE: S100-S200+ system pages are a separate uSystem module within
   uConnect/ and are NOT related to Teletext. They are system fallback
   pages with their own style/CSS.

   Viewport presets (set via Display Settings):
     28×28 — 1:1 square
     48×36 — 4:3 (default for teletext)
     64×36 — 16:9 widescreen
   ═══════════════════════════════════════════════════════════════════ */

import {
  GridBuffer,
  GridCell,
  createBuffer,
  createCell,
  cloneBuffer,
  getDimensions,
} from './GridCell'
import { writeString, fill } from './GridTransform'
import { cityRegistry } from './CityRegistry'
import type { CityMarker } from './CityRegistry'
import { locationStore } from './LocationStore'

// ─── Standard page buffer size (48×36 = 4:3, the default teletext preset) ──
const PAGE_COLS = 48
const PAGE_ROWS = 36

// ─── Page Metadata ───────────────────────────────────────────────────

export interface TeletextPageMeta {
  pageNumber: number
  title: string
  subtitle?: string
  lastUpdated?: number  // timestamp
}

export interface TeletextPage {
  meta: TeletextPageMeta
  buffer: GridBuffer  // 48×36 (4:3 default)
}

// ─── Page Store ──────────────────────────────────────────────────────

export class TeletextPageStore {
  private pages: Map<number, TeletextPage> = new Map()

  constructor() {
    this.seedBuiltinPages()
  }

  /** Get a page by number. Returns undefined if not found. */
  get(pageNumber: number): TeletextPage | undefined {
    return this.pages.get(pageNumber)
  }

  /** Set a page. */
  set(pageNumber: number, page: TeletextPage): void {
    this.pages.set(pageNumber, page)
  }

  /** Check if a page exists. */
  has(pageNumber: number): boolean {
    return this.pages.has(pageNumber)
  }

  /** Get all page numbers. */
  getPageNumbers(): number[] {
    return Array.from(this.pages.keys()).sort()
  }

  /** Remove a page. */
  delete(pageNumber: number): void {
    this.pages.delete(pageNumber)
  }

  /** Clear all pages. */
  clear(): void {
    this.pages.clear()
  }

  // ─── Snackbar API Integration ────────────────────────────────────

  private snackbarUrl = 'http://127.0.0.1:8484'

  /** Set the Snackbar API base URL (e.g. for custom ports). */
  setSnackbarUrl(url: string): void {
    this.snackbarUrl = url
  }

  /** Fetch a page from the Snackbar Ceefax API and store it locally.
   *  Returns the page if found, or undefined if the API call fails. */
  async fetchFromSnackbar(pageNumber: number): Promise<TeletextPage | undefined> {
    try {
      const resp = await fetch(`${this.snackbarUrl}/api/ceefax/page/${pageNumber}`)
      if (!resp.ok) return undefined
      const data = await resp.json()
      const apiPage = data.page
      if (!apiPage) return undefined

      // Convert API buffer (array of arrays) to GridBuffer
      const buf = createBuffer(PAGE_COLS, PAGE_ROWS)
      const rawBuffer: any[][] = apiPage.buffer || []
      for (let row = 0; row < Math.min(rawBuffer.length, PAGE_ROWS); row++) {
        const rawRow = rawBuffer[row]
        if (!rawRow) continue
        for (let col = 0; col < Math.min(rawRow.length, PAGE_COLS); col++) {
          const cellVal = rawRow[col]
          if (typeof cellVal === 'number') {
            buf[row][col] = createCell(String.fromCharCode(cellVal), 7, 0)
          } else if (typeof cellVal === 'object' && cellVal !== null) {
            const obj = cellVal as Record<string, any>
            buf[row][col] = createCell(
              obj.char !== undefined ? String.fromCharCode(obj.char) : ' ',
              obj.fg ?? 7,
              obj.bg ?? 0,
              obj.bold ?? false,
              obj.flash ?? false,
              obj.doubleHeight ?? false,
              obj.doubleWidth ?? false,
            )
          }
        }
      }

      const page: TeletextPage = {
        meta: {
          pageNumber: apiPage.number,
          title: apiPage.title || `Page ${apiPage.number}`,
          lastUpdated: apiPage.last_updated ? new Date(apiPage.last_updated).getTime() : undefined,
        },
        buffer: buf,
      }
      this.set(pageNumber, page)
      return page
    } catch (err) {
      console.warn(`[TeletextPageStore] Failed to fetch page ${pageNumber} from Snackbar:`, err)
      return undefined
    }
  }

  /** Refresh all pages from the Snackbar API.
   *  Fetches the page list, then fetches each page individually.
   *  Returns the count of pages successfully refreshed. */
  async refreshFromApi(): Promise<number> {
    try {
      const resp = await fetch(`${this.snackbarUrl}/api/ceefax/pages`)
      if (!resp.ok) return 0
      const data = await resp.json()
      const pages: Array<{ number: number }> = data.pages || []
      let count = 0
      for (const p of pages) {
        const page = await this.fetchFromSnackbar(p.number)
        if (page) count++
      }
      return count
    } catch (err) {
      console.warn('[TeletextPageStore] Failed to refresh pages from Snackbar:', err)
      return 0
    }
  }

  /** Push a feed item to the Snackbar Ceefax feed API. */
  async pushFeedItem(source: string, title: string, body: string, page: number = 500): Promise<boolean> {
    try {
      const resp = await fetch(`${this.snackbarUrl}/api/ceefax/feed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, title, body, page }),
      })
      return resp.ok
    } catch (err) {
      console.warn('[TeletextPageStore] Failed to push feed item:', err)
      return false
    }
  }

  /** Get the latest feed items from the Snackbar Ceefax feed API. */
  async getLatestFeedItems(limit: number = 10): Promise<Array<{ id: string; source: string; title: string; body: string; timestamp: string; page: number }>> {
    try {
      const resp = await fetch(`${this.snackbarUrl}/api/ceefax/feed/latest?limit=${limit}`)
      if (!resp.ok) return []
      const data = await resp.json()
      return data.items || []
    } catch (err) {
      console.warn('[TeletextPageStore] Failed to get feed items:', err)
      return []
    }
  }

  // ─── Built-in Pages ──────────────────────────────────────────────

  private seedBuiltinPages(): void {
    // P100-P199: Index/Welcome, System Status, Help, About
    this.set(100, this.buildWelcomePage())
    this.set(101, this.buildSystemStatusPage())
    this.set(102, this.buildHelpPage())
    this.set(103, this.buildAboutPage())

    // P200-P299: News, Dev Log, Changelog
    this.set(200, this.buildNewsFeedPage())
    this.set(201, this.buildDevLogPage())
    this.set(202, this.buildChangelogPage())

    // P300-P399: Surface Status
    this.set(300, this.buildSurfaceStatusPage())
    this.set(301, this.buildUCode1StatusPage())
    this.set(302, this.buildUServerStatusPage())
    this.set(303, this.buildUConnectStatusPage())

    // P340-P349: City pages (one per region)
    this.set(340, this.buildCityPage('oceania'))
    this.set(341, this.buildCityPage('southeast_asia'))
    this.set(342, this.buildCityPage('east_asia'))
    this.set(343, this.buildCityPage('south_asia'))
    this.set(344, this.buildCityPage('europe'))
    this.set(345, this.buildCityPage('north_america'))
    this.set(346, this.buildCityPage('south_america'))
    this.set(347, this.buildCityPage('africa'))
    this.set(348, this.buildCityPage('middle_east'))

    // P350: Location status page (dynamic, shows current location)
    this.set(350, this.buildLocationPage())

    // P400-P499: Weather, Time, Date
    this.set(400, this.buildWeatherPage())
    this.set(401, this.buildTimeDatePage())

    // P500-P599: Live feed pages (built dynamically from Snackbar API)
    // These are populated on first access via fetchFromSnackbar or refreshFromApi
    // Static placeholders are not seeded — the auto-rotate in TeletextPanel
    // fetches them from the Snackbar Ceefax API which builds them dynamically.

    // P600-P699: Gallery/Design showcase
    this.set(600, this.buildGalleryPage())
    this.set(601, this.buildDesignShowcasePage())
    this.set(602, this.buildBobGalleryPage())
    this.set(603, this.buildBobGalleryPage2())
    this.set(604, this.buildBobGalleryPage3())
    this.set(605, this.buildBobGalleryPage4())
    this.set(606, this.buildBobGalleryPage5())
    this.set(607, this.buildBobGalleryPage6())
    this.set(608, this.buildBobGalleryPage7())
    this.set(609, this.buildBobGalleryPage8())
    this.set(610, this.buildBobGalleryPage9())

    // P800-P899: Test cards, colour bars, diagnostics
    this.set(800, this.buildDiagnosticsPage())
    this.set(888, this.buildColourTestCard())
  }

  // ─── P100-P199: Index/Welcome, System Status, Help, About ────────

  private buildWelcomePage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    // Header bar (row 0)
    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)  // White on blue
    buf = writeString(buf, 2, 0, 'CEETEX 100', 7, 4)
    buf = writeString(buf, 28, 0, 'P100', 7, 4)

    // Title (row 2-5)
    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║     WELCOME TO CEETEX       ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '║   Teletext Information System ║', 3, 0, true)
    buf = writeString(buf, 4, 5, '╚══════════════════════════════╝', 3, 0, true)

    // Navigation guide
    buf = writeString(buf, 4, 8, 'PAGE  NAVIGATION', 2, 0, true)
    buf = writeString(buf, 4, 9, '100  Welcome Page', 7, 0)
    buf = writeString(buf, 4, 10, '101  System Status', 7, 0)
    buf = writeString(buf, 4, 11, '102  Help', 7, 0)
    buf = writeString(buf, 4, 12, '103  About Ceetex', 7, 0)
    buf = writeString(buf, 4, 13, '200  News Feed', 7, 0)
    buf = writeString(buf, 4, 14, '201  Dev Log', 7, 0)
    buf = writeString(buf, 4, 15, '202  Changelog', 7, 0)
    buf = writeString(buf, 4, 16, '300  Surface Status', 7, 0)
    buf = writeString(buf, 4, 17, '400  Weather', 7, 0)
    buf = writeString(buf, 4, 18, '600  Gallery', 7, 0)
    buf = writeString(buf, 4, 19, '888  Colour Test Card', 7, 0)

    buf = writeString(buf, 4, 21, 'CONTROLS', 2, 0, true)
    buf = writeString(buf, 4, 22, 'Enter 3-digit page number to navigate', 7, 0)

    // Status row (row 24)
    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)  // White on red
    buf = writeString(buf, 2, 24, 'CEETEX 100  Welcome  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 100, title: 'Welcome' }, buffer: buf }
  }

  private buildSystemStatusPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 101', 7, 4)
    buf = writeString(buf, 28, 0, 'P101', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       SYSTEM STATUS         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'uCode1 Emulator:', 2, 0, true)
    buf = writeString(buf, 22, 6, 'RUNNING', 2, 0)

    buf = writeString(buf, 4, 8, 'uConnect Hub:', 2, 0, true)
    buf = writeString(buf, 22, 8, 'ONLINE', 2, 0)

    buf = writeString(buf, 4, 10, 'uServer API:', 2, 0, true)
    buf = writeString(buf, 22, 10, 'ONLINE', 2, 0)

    buf = writeString(buf, 4, 12, 'GridUI Surface:', 2, 0, true)
    buf = writeString(buf, 22, 12, 'ACTIVE', 2, 0)

    buf = writeString(buf, 4, 14, 'Memory Used:', 2, 0, true)
    buf = writeString(buf, 22, 14, '42%', 7, 0)

    buf = writeString(buf, 4, 16, 'CPU Load:', 2, 0, true)
    buf = writeString(buf, 22, 16, '12%', 7, 0)

    buf = writeString(buf, 4, 18, 'Uptime:', 2, 0, true)
    buf = writeString(buf, 22, 18, '14d 6h 32m', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 101  System Status  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 101, title: 'System Status' }, buffer: buf }
  }

  private buildHelpPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 102', 7, 4)
    buf = writeString(buf, 28, 0, 'P102', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║           HELP              ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'NAVIGATION', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Type any 3-digit page number to jump', 7, 0)
    buf = writeString(buf, 4, 8, 'directly to that page.', 7, 0)

    buf = writeString(buf, 4, 10, 'PAGE INDEX', 2, 0, true)
    buf = writeString(buf, 4, 11, '100-199  Index & System Info', 7, 0)
    buf = writeString(buf, 4, 12, '200-299  News & Updates', 7, 0)
    buf = writeString(buf, 4, 13, '300-399  Surface Status', 7, 0)
    buf = writeString(buf, 4, 14, '400-499  Weather & Time', 7, 0)
    buf = writeString(buf, 4, 15, '500-599  Sub-pages', 7, 0)
    buf = writeString(buf, 4, 16, '600-699  Gallery', 7, 0)
    buf = writeString(buf, 4, 17, '800-899  Test Cards & Diagnostics', 7, 0)

    buf = writeString(buf, 4, 19, 'DISPLAY', 2, 0, true)
    buf = writeString(buf, 4, 20, 'Use the Display Settings button to', 7, 0)
    buf = writeString(buf, 4, 21, 'adjust viewport size and border mode.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 102  Help  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 102, title: 'Help' }, buffer: buf }
  }

  private buildAboutPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 103', 7, 4)
    buf = writeString(buf, 28, 0, 'P103', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║      ABOUT CEETEX           ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Ceetex is a teletext-style', 7, 0)
    buf = writeString(buf, 4, 7, 'information system built on', 7, 0)
    buf = writeString(buf, 4, 8, 'the Grid Algebra rendering', 7, 0)
    buf = writeString(buf, 4, 9, 'engine.', 7, 0)

    buf = writeString(buf, 4, 11, 'Version: 2.0.0', 7, 0)
    buf = writeString(buf, 4, 12, 'Engine: Grid Algebra v3.1', 7, 0)
    buf = writeString(buf, 4, 13, 'Font: Bedstead (teletext)', 7, 0)
    buf = writeString(buf, 4, 14, 'Palette: Unified Dark', 7, 0)

    buf = writeString(buf, 4, 16, 'Inspired by Ceefax, the BBC\'s', 7, 0)
    buf = writeString(buf, 4, 17, 'original teletext service', 7, 0)
    buf = writeString(buf, 4, 18, '(1974-2012).', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 103  About  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 103, title: 'About Ceetex' }, buffer: buf }
  }

  // ─── P200-P299: News, Dev Log, Changelog ─────────────────────────

  private buildNewsFeedPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 200', 7, 4)
    buf = writeString(buf, 28, 0, 'P200', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║         NEWS FEED           ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, '>> Grid Algebra Core Complete', 2, 0, true)
    buf = writeString(buf, 4, 7, '  GridCell, GridTransform, ColourPalette', 7, 0)
    buf = writeString(buf, 4, 8, '  and TeletextPage modules built.', 7, 0)

    buf = writeString(buf, 4, 10, '>> Teletext Panel In Progress', 2, 0, true)
    buf = writeString(buf, 4, 11, '  New TeletextPanel using grid-algebra', 7, 0)
    buf = writeString(buf, 4, 12, '  with 3-digit page navigation.', 7, 0)

    buf = writeString(buf, 4, 14, '>> Terminal Refactoring', 2, 0, true)
    buf = writeString(buf, 4, 15, '  TerminalPanel now uses GridBuffer', 7, 0)
    buf = writeString(buf, 4, 16, '  internally for consistent rendering.', 7, 0)

    buf = writeString(buf, 4, 18, '>> Next: GridWidget Component', 2, 0, true)
    buf = writeString(buf, 4, 19, '  Embeddable grid renderer for ProseUI', 7, 0)
    buf = writeString(buf, 4, 20, '  and Dashboard panels.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 200  News Feed  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 200, title: 'News Feed' }, buffer: buf }
  }

  private buildDevLogPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 201', 7, 4)
    buf = writeString(buf, 28, 0, 'P201', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║         DEV LOG             ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, '2026-06-11  Unified palette', 2, 0, true)
    buf = writeString(buf, 4, 7, '  Replaced all retro palettes with', 7, 0)
    buf = writeString(buf, 4, 8, '  single Bootstrap/GitHub Dark palette.', 7, 0)

    buf = writeString(buf, 4, 10, '2026-06-10  Teletext pages', 2, 0, true)
    buf = writeString(buf, 4, 11, '  Restored P100-P899 page range.', 7, 0)
    buf = writeString(buf, 4, 12, '  S100-S200 kept as separate uSystem.', 7, 0)

    buf = writeString(buf, 4, 14, '2026-06-09  Font update', 2, 0, true)
    buf = writeString(buf, 4, 15, '  Bedstead for teletext, PetMe128', 7, 0)
    buf = writeString(buf, 4, 16, '  for terminal display.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 201  Dev Log  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 201, title: 'Dev Log' }, buffer: buf }
  }

  private buildChangelogPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 202', 7, 4)
    buf = writeString(buf, 28, 0, 'P202', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║        CHANGELOG            ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'v2.0.0 (2026-06-11)', 3, 0, true)
    buf = writeString(buf, 4, 7, '- Unified colour palette', 7, 0)
    buf = writeString(buf, 4, 8, '- Bedstead font for teletext', 7, 0)
    buf = writeString(buf, 4, 9, '- Full P100-P899 page range', 7, 0)
    buf = writeString(buf, 4, 10, '- Vault sidebar integration', 7, 0)
    buf = writeString(buf, 4, 11, '- Grid Editor layout restructure', 7, 0)

    buf = writeString(buf, 4, 13, 'v1.0.0 (2026-05-20)', 3, 0, true)
    buf = writeString(buf, 4, 14, '- Initial Grid Algebra release', 7, 0)
    buf = writeString(buf, 4, 15, '- Teletext panel with page nav', 7, 0)
    buf = writeString(buf, 4, 16, '- C64 BASIC terminal', 7, 0)
    buf = writeString(buf, 4, 17, '- Grid Editor with layers', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 202  Changelog  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 202, title: 'Changelog' }, buffer: buf }
  }

  // ─── P300-P399: Surface Status ───────────────────────────────────

  private buildSurfaceStatusPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 300', 7, 4)
    buf = writeString(buf, 28, 0, 'P300', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║      SURFACE STATUS         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Surface          Status    Port', 2, 0, true)
    buf = writeString(buf, 4, 7, 'GridUI           RUNNING   5178', 2, 0)
    buf = writeString(buf, 4, 8, 'ProseUI          RUNNING   5184', 7, 0)
    buf = writeString(buf, 4, 9, 'ChatUI           RUNNING   5182', 7, 0)
    buf = writeString(buf, 4, 10, 'BrowserUI        RUNNING   5179', 7, 0)
    buf = writeString(buf, 4, 11, 'uServer          ONLINE    EMBED', 7, 0)
    buf = writeString(buf, 4, 12, 'Homenest         STOPPED   5190', 1, 0)

    buf = writeString(buf, 4, 14, 'See P301-P303 for detailed', 7, 0)
    buf = writeString(buf, 4, 15, 'status per surface.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 300  Surface Status  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 300, title: 'Surface Status' }, buffer: buf }
  }

  private buildUCode1StatusPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 301', 7, 4)
    buf = writeString(buf, 28, 0, 'P301', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║     UCODE1 EMULATOR         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Status: RUNNING', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Arch: MOS 6502', 7, 0)
    buf = writeString(buf, 4, 8, 'Clock: 1 MHz', 7, 0)
    buf = writeString(buf, 4, 9, 'RAM: 64 KB', 7, 0)
    buf = writeString(buf, 4, 10, 'Cycles: 1,234,567', 7, 0)

    buf = writeString(buf, 4, 12, 'Loaded Programs:', 2, 0, true)
    buf = writeString(buf, 4, 13, '- BASIC V2 Interpreter', 7, 0)
    buf = writeString(buf, 4, 14, '- Monitor/Debugger', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 301  uCode1 Status  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 301, title: 'uCode1 Status' }, buffer: buf }
  }

  private buildUServerStatusPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 302', 7, 4)
    buf = writeString(buf, 28, 0, 'P302', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       USERVER STATUS        ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Status: ONLINE', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Host: 192.168.20.11', 7, 0)
    buf = writeString(buf, 4, 8, 'Snackbar: 8484', 7, 0)
    buf = writeString(buf, 4, 9, 'Secret Server: 30001', 7, 0)
    buf = writeString(buf, 4, 10, 'Hivemind: 8485', 7, 0)

    buf = writeString(buf, 4, 12, 'Services:', 2, 0, true)
    buf = writeString(buf, 4, 13, '- OAuth Provider', 7, 0)
    buf = writeString(buf, 4, 14, '- Surface Registry', 7, 0)
    buf = writeString(buf, 4, 15, '- Sync Service', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 302  uServer Status  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 302, title: 'uServer Status' }, buffer: buf }
  }

  private buildUConnectStatusPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 303', 7, 4)
    buf = writeString(buf, 28, 0, 'P303', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║      UCONNECT STATUS        ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Status: ONLINE', 2, 0, true)
    buf = writeString(buf, 4, 7, 'UI Hub: Active', 7, 0)
    buf = writeString(buf, 4, 8, 'Surfaces: 6 registered', 7, 0)
    buf = writeString(buf, 4, 9, 'Theme: USX Dark', 7, 0)

    buf = writeString(buf, 4, 11, 'Active Surfaces:', 2, 0, true)
    buf = writeString(buf, 4, 12, '- GridUI (uCode1)', 7, 0)
    buf = writeString(buf, 4, 13, '- ProseUI (uCode2)', 7, 0)
    buf = writeString(buf, 4, 14, '- ChatUI', 7, 0)
    buf = writeString(buf, 4, 15, '- BrowserUI', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 303  uConnect Status  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 303, title: 'uConnect Status' }, buffer: buf }
  }

  // ─── P400-P499: Weather, Time, Date ──────────────────────────────

  private buildWeatherPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 400', 7, 4)
    buf = writeString(buf, 28, 0, 'P400', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║         WEATHER             ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Brisbane, Australia', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Partly Cloudy', 7, 0)
    buf = writeString(buf, 4, 8, 'Temp: 22 C', 7, 0)
    buf = writeString(buf, 4, 9, 'Humidity: 65%', 7, 0)
    buf = writeString(buf, 4, 10, 'Wind: 15 km/h SE', 7, 0)

    buf = writeString(buf, 4, 12, 'Forecast:', 2, 0, true)
    buf = writeString(buf, 4, 13, 'Wed: 24 C  Sunny', 7, 0)
    buf = writeString(buf, 4, 14, 'Thu: 23 C  Partly Cloudy', 7, 0)
    buf = writeString(buf, 4, 15, 'Fri: 21 C  Showers', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 400  Weather  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 400, title: 'Weather' }, buffer: buf }
  }

  private buildTimeDatePage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 401', 7, 4)
    buf = writeString(buf, 28, 0, 'P401', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║      TIME AND DATE          ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Current Time:', 2, 0, true)
    buf = writeString(buf, 22, 6, '00:00:00 UTC+10', 7, 0)

    buf = writeString(buf, 4, 8, 'Current Date:', 2, 0, true)
    buf = writeString(buf, 22, 8, 'Mon 11 Jun 2026', 7, 0)

    buf = writeString(buf, 4, 10, 'Timezone:', 2, 0, true)
    buf = writeString(buf, 22, 10, 'AEST (Brisbane)', 7, 0)

    buf = writeString(buf, 4, 12, 'Unix Timestamp:', 2, 0, true)
    buf = writeString(buf, 22, 12, '1780000000', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 401  Time & Date  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 401, title: 'Time & Date' }, buffer: buf }
  }

  // ─── P500-P599: Sub-page content ─────────────────────────────────

  private buildSubPage500(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 500', 7, 4)
    buf = writeString(buf, 28, 0, 'P500', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       SUB-PAGE 500          ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'This is a sub-page for deeper', 7, 0)
    buf = writeString(buf, 4, 7, 'content that extends the main', 7, 0)
    buf = writeString(buf, 4, 8, 'page categories.', 7, 0)

    buf = writeString(buf, 4, 10, 'Sub-pages can be used for:', 2, 0, true)
    buf = writeString(buf, 4, 11, '- Extended articles', 7, 0)
    buf = writeString(buf, 4, 12, '- Detailed status breakdowns', 7, 0)
    buf = writeString(buf, 4, 13, '- Multi-page features', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 500  Sub-page 500  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 500, title: 'Sub-page 500' }, buffer: buf }
  }

  private buildSubPage501(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 501', 7, 4)
    buf = writeString(buf, 28, 0, 'P501', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       SUB-PAGE 501          ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Extended content for page 500.', 7, 0)
    buf = writeString(buf, 4, 8, 'More detailed information can', 7, 0)
    buf = writeString(buf, 4, 9, 'be placed here.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 501  Sub-page 501  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 501, title: 'Sub-page 501' }, buffer: buf }
  }

  // ─── P600-P699: Gallery/Design showcase ──────────────────────────

  private buildGalleryPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 600', 7, 4)
    buf = writeString(buf, 28, 0, 'P600', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║         GALLERY             ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Ceefax In-Vision Gallery', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Showcasing teletext-style', 7, 0)
    buf = writeString(buf, 4, 8, 'design and layout examples.', 7, 0)

    buf = writeString(buf, 4, 10, 'Features:', 2, 0, true)
    buf = writeString(buf, 4, 11, '- Colour block layouts', 7, 0)
    buf = writeString(buf, 4, 12, '- Box-drawn diagrams', 7, 0)
    buf = writeString(buf, 4, 13, '- Character map previews', 7, 0)
    buf = writeString(buf, 4, 14, '- Font sample pages', 7, 0)

    buf = writeString(buf, 4, 16, 'See P601 for design showcase.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 600  Gallery  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 600, title: 'Gallery' }, buffer: buf }
  }

  private buildDesignShowcasePage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 601', 7, 4)
    buf = writeString(buf, 28, 0, 'P601', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║     DESIGN SHOWCASE         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Teletext Design Elements:', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Header bars with colour blocks', 7, 0)
    buf = writeString(buf, 4, 8, 'Box-drawn borders and separators', 7, 0)
    buf = writeString(buf, 4, 9, 'Colour-coded category labels', 7, 0)
    buf = writeString(buf, 4, 10, 'Status row with page info', 7, 0)

    buf = writeString(buf, 4, 12, 'Colour Palette (Unified Dark):', 2, 0, true)
    buf = writeString(buf, 4, 13, '  Bootstrap/GitHub Dark', 7, 0)
    buf = writeString(buf, 4, 14, '  16-colour ANSI-compatible', 7, 0)
    buf = writeString(buf, 4, 15, '  Optimised for teletext display', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 601  Design Showcase  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 601, title: 'Design Showcase' }, buffer: buf }
  }

  // ─── P602-P610: Bob Gallery Pages ────────────────────────────────

  private buildBobGalleryPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 602', 7, 4)
    buf = writeString(buf, 28, 0, 'P602', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       BOB GALLERY 1         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'uVector Bob Showcase', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Inline sprites generated from', 7, 0)
    buf = writeString(buf, 4, 8, 'text prompts via uVector SVG engine.', 7, 0)

    buf = writeString(buf, 4, 10, 'Available Bobs (P602-P610):', 2, 0, true)
    buf = writeString(buf, 4, 11, '602  Heart, Star, Rocket, Settings', 7, 0)
    buf = writeString(buf, 4, 12, '603  User, Home, Search, Mail', 7, 0)
    buf = writeString(buf, 4, 13, '604  Bell, Clock, Calendar, Bookmark', 7, 0)
    buf = writeString(buf, 4, 14, '605  Lightbulb, Check, Cross, Plus', 7, 0)
    buf = writeString(buf, 4, 15, '606  Arrows (Up, Down, Left, Right)', 7, 0)
    buf = writeString(buf, 4, 16, '607  Lock, Cloud, Download, Upload', 7, 0)
    buf = writeString(buf, 4, 17, '608  Trash, Edit, Eye, Music', 7, 0)
    buf = writeString(buf, 4, 18, '609  Play, Pause, Stop, Refresh', 7, 0)
    buf = writeString(buf, 4, 19, '610  Share, Link, Camera, File', 7, 0)

    buf = writeString(buf, 4, 21, 'Use :bob:name: shortcode in ProseUI', 7, 0)
    buf = writeString(buf, 4, 22, 'editor to insert any bob inline.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 602  Bob Gallery 1  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 602, title: 'Bob Gallery 1' }, buffer: buf }
  }

  private buildBobGalleryPage2(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 603', 7, 4)
    buf = writeString(buf, 28, 0, 'P603', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       BOB GALLERY 2         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'User & Navigation Bobs', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Shortcodes: :bob:user: :bob:home:', 7, 0)
    buf = writeString(buf, 4, 8, '            :bob:search: :bob:mail:', 7, 0)

    buf = writeString(buf, 4, 10, 'Usage in ProseUI:', 2, 0, true)
    buf = writeString(buf, 4, 11, 'Type :bob:name: in the editor to', 7, 0)
    buf = writeString(buf, 4, 12, 'insert an inline bob. Use optional', 7, 0)
    buf = writeString(buf, 4, 13, 'size/style overrides:', 7, 0)
    buf = writeString(buf, 4, 14, '  :bob:heart:32x32:full_color:', 7, 0)

    buf = writeString(buf, 4, 16, 'Styles:', 2, 0, true)
    buf = writeString(buf, 4, 17, '  mono_chrome  - Black & white', 7, 0)
    buf = writeString(buf, 4, 18, '  teletext     - Ceefax palette', 7, 0)
    buf = writeString(buf, 4, 19, '  full_color   - Full colour', 7, 0)

    buf = writeString(buf, 4, 21, 'Sizes: 16x16 (default), 32x32', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 603  Bob Gallery 2  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 603, title: 'Bob Gallery 2' }, buffer: buf }
  }

  private buildBobGalleryPage3(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 604', 7, 4)
    buf = writeString(buf, 28, 0, 'P604', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       BOB GALLERY 3         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Notification & Time Bobs', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Shortcodes: :bob:bell: :bob:clock:', 7, 0)
    buf = writeString(buf, 4, 8, '            :bob:calendar: :bob:bookmark:', 7, 0)

    buf = writeString(buf, 4, 10, 'Keyboard Shortcut:', 2, 0, true)
    buf = writeString(buf, 4, 11, 'Press Ctrl+Shift+B in the ProseUI', 7, 0)
    buf = writeString(buf, 4, 12, 'editor to open the bob picker.', 7, 0)

    buf = writeString(buf, 4, 14, 'Autocomplete:', 2, 0, true)
    buf = writeString(buf, 4, 15, 'Type :bob: in the editor to trigger', 7, 0)
    buf = writeString(buf, 4, 16, 'autocomplete with filtered suggestions.', 7, 0)

    buf = writeString(buf, 4, 18, 'Download:', 2, 0, true)
    buf = writeString(buf, 4, 19, 'Hover over any bob to see SVG/PNG', 7, 0)
    buf = writeString(buf, 4, 20, 'download buttons.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 604  Bob Gallery 3  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 604, title: 'Bob Gallery 3' }, buffer: buf }
  }

  private buildBobGalleryPage4(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 605', 7, 4)
    buf = writeString(buf, 28, 0, 'P605', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       BOB GALLERY 4         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Action & Status Bobs', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Shortcodes: :bob:lightbulb: :bob:check:', 7, 0)
    buf = writeString(buf, 4, 8, '            :bob:cross: :bob:plus:', 7, 0)

    buf = writeString(buf, 4, 10, 'Bob Generation:', 2, 0, true)
    buf = writeString(buf, 4, 11, 'Bobs are generated on-demand by the', 7, 0)
    buf = writeString(buf, 4, 12, 'uVector SVG engine running on Forge.', 7, 0)
    buf = writeString(buf, 4, 13, 'Results are cached in memory for', 7, 0)
    buf = writeString(buf, 4, 14, 'fast subsequent access.', 7, 0)

    buf = writeString(buf, 4, 16, 'Fallback:', 2, 0, true)
    buf = writeString(buf, 4, 17, 'If uVector is unavailable, bobs', 7, 0)
    buf = writeString(buf, 4, 18, 'fall back to a placeholder SVG', 7, 0)
    buf = writeString(buf, 4, 19, 'showing the first 2 characters.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 605  Bob Gallery 4  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 605, title: 'Bob Gallery 4' }, buffer: buf }
  }

  private buildBobGalleryPage5(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 606', 7, 4)
    buf = writeString(buf, 28, 0, 'P606', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       BOB GALLERY 5         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Direction & Navigation Bobs', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Shortcodes: :bob:arrow-up: :bob:arrow-down:', 7, 0)
    buf = writeString(buf, 4, 8, '            :bob:arrow-left: :bob:arrow-right:', 7, 0)

    buf = writeString(buf, 4, 10, 'Symbol Registry:', 2, 0, true)
    buf = writeString(buf, 4, 11, 'Bobs can also be resolved from the', 7, 0)
    buf = writeString(buf, 4, 12, 'USX symbol registry via shortcodes.', 7, 0)
    buf = writeString(buf, 4, 13, 'Registered symbols take priority', 7, 0)
    buf = writeString(buf, 4, 14, 'over uVector generation.', 7, 0)

    buf = writeString(buf, 4, 16, 'See P602 for full bob index.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 606  Bob Gallery 5  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 606, title: 'Bob Gallery 5' }, buffer: buf }
  }

  private buildBobGalleryPage6(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 607', 7, 4)
    buf = writeString(buf, 28, 0, 'P607', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       BOB GALLERY 6         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Security & Storage Bobs', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Shortcodes: :bob:lock: :bob:unlock:', 7, 0)
    buf = writeString(buf, 4, 8, '            :bob:cloud: :bob:download:', 7, 0)
    buf = writeString(buf, 4, 9, '            :bob:upload:', 7, 0)

    buf = writeString(buf, 4, 11, 'Bob Export:', 2, 0, true)
    buf = writeString(buf, 4, 12, 'Hover over any bob to reveal', 7, 0)
    buf = writeString(buf, 4, 13, 'SVG and PNG download buttons.', 7, 0)
    buf = writeString(buf, 4, 14, 'PNG is rendered at 4x resolution', 7, 0)
    buf = writeString(buf, 4, 15, 'for crisp output.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 607  Bob Gallery 6  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 607, title: 'Bob Gallery 6' }, buffer: buf }
  }

  private buildBobGalleryPage7(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 608', 7, 4)
    buf = writeString(buf, 28, 0, 'P608', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       BOB GALLERY 7         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Edit & Media Bobs', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Shortcodes: :bob:trash: :bob:edit:', 7, 0)
    buf = writeString(buf, 4, 8, '            :bob:pencil: :bob:eye:', 7, 0)
    buf = writeString(buf, 4, 9, '            :bob:eye-off: :bob:music:', 7, 0)

    buf = writeString(buf, 4, 11, 'Bob Picker:', 2, 0, true)
    buf = writeString(buf, 4, 12, 'Open the bob picker from the', 7, 0)
    buf = writeString(buf, 4, 13, 'editor toolbar (Bob button) or', 7, 0)
    buf = writeString(buf, 4, 14, 'press Ctrl+Shift+B.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 608  Bob Gallery 7  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 608, title: 'Bob Gallery 7' }, buffer: buf }
  }

  private buildBobGalleryPage8(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 609', 7, 4)
    buf = writeString(buf, 28, 0, 'P609', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       BOB GALLERY 8         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Media Control Bobs', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Shortcodes: :bob:play: :bob:pause:', 7, 0)
    buf = writeString(buf, 4, 8, '            :bob:stop: :bob:refresh:', 7, 0)
    buf = writeString(buf, 4, 9, '            :bob:sync:', 7, 0)

    buf = writeString(buf, 4, 11, 'Style Overrides:', 2, 0, true)
    buf = writeString(buf, 4, 12, '  :bob:heart:32x32:full_color:', 7, 0)
    buf = writeString(buf, 4, 13, '  :bob:star:16x16:teletext:', 7, 0)
    buf = writeString(buf, 4, 14, '  :bob:rocket:32x32:mono_chrome:', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 609  Bob Gallery 8  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 609, title: 'Bob Gallery 8' }, buffer: buf }
  }

  private buildBobGalleryPage9(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 610', 7, 4)
    buf = writeString(buf, 28, 0, 'P610', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       BOB GALLERY 9         ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'Share & File Bobs', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Shortcodes: :bob:share: :bob:link:', 7, 0)
    buf = writeString(buf, 4, 8, '            :bob:paperclip: :bob:camera:', 7, 0)
    buf = writeString(buf, 4, 9, '            :bob:image: :bob:file:', 7, 0)
    buf = writeString(buf, 4, 10, '            :bob:folder: :bob:tag:', 7, 0)

    buf = writeString(buf, 4, 12, 'All bobs are generated by uVector', 2, 0, true)
    buf = writeString(buf, 4, 13, 'on Forge (192.168.20.11:8484).', 7, 0)
    buf = writeString(buf, 4, 14, 'The SVG engine converts text prompts', 7, 0)
    buf = writeString(buf, 4, 15, 'into clean, minimal icon SVGs.', 7, 0)

    buf = writeString(buf, 4, 17, 'See P100 for full page index.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 610  Bob Gallery 9  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 610, title: 'Bob Gallery 9' }, buffer: buf }
  }

  // ─── P800-P899: Test cards, colour bars, diagnostics ─────────────

  private buildDiagnosticsPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 800', 7, 4)
    buf = writeString(buf, 28, 0, 'P800', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║       DIAGNOSTICS           ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    buf = writeString(buf, 4, 6, 'System Diagnostics', 2, 0, true)
    buf = writeString(buf, 4, 7, 'Grid Algebra Engine: OK', 2, 0)
    buf = writeString(buf, 4, 8, 'Colour Palette: OK', 7, 0)
    buf = writeString(buf, 4, 9, 'Teletext Page Store: OK', 7, 0)
    buf = writeString(buf, 4, 10, 'GridBuffer Renderer: OK', 7, 0)
    buf = writeString(buf, 4, 11, 'Font Loading: OK', 7, 0)

    buf = writeString(buf, 4, 13, 'Page Count: 16', 7, 0)
    buf = writeString(buf, 4, 14, 'Buffer Size: 48x36', 7, 0)
    buf = writeString(buf, 4, 15, 'Colour Depth: 16 colours', 7, 0)

    buf = writeString(buf, 4, 17, 'See P888 for Colour Test Card.', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 800  Diagnostics  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 800, title: 'Diagnostics' }, buffer: buf }
  }

  // ─── P340-P349: City pages ──────────────────────────────────────

  private buildCityPage(region: string): TeletextPage {
    const regionNames: Record<string, string> = {
      oceania: 'Oceania',
      southeast_asia: 'Southeast Asia',
      east_asia: 'East Asia',
      south_asia: 'South Asia',
      europe: 'Europe',
      north_america: 'North America',
      south_america: 'South America',
      africa: 'Africa',
      middle_east: 'Middle East',
    }

    const regionPageNumbers: Record<string, number> = {
      oceania: 340,
      southeast_asia: 341,
      east_asia: 342,
      south_asia: 343,
      europe: 344,
      north_america: 345,
      south_america: 346,
      africa: 347,
      middle_east: 348,
    }

    const pageNum = regionPageNumbers[region] || 340
    const regionName = regionNames[region] || region
    const cities = cityRegistry.getByRegion(region)

    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    // Header
    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, `CEETEX ${pageNum}`, 7, 4)
    buf = writeString(buf, 28, 0, `P${pageNum}`, 7, 4)

    // Title
    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, `║  ${regionName.padEnd(28)}║`, 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    // City list
    buf = writeString(buf, 2, 6, 'CITY', 2, 0, true)
    buf = writeString(buf, 18, 6, 'COUNTRY', 2, 0, true)
    buf = writeString(buf, 30, 6, 'PAGE', 2, 0, true)

    cities.forEach((city, i) => {
      const row = 7 + i
      if (row >= 23) return  // Don't overflow the page
      buf = writeString(buf, 2, row, city.name, 7, 0)
      buf = writeString(buf, 18, row, city.region, 7, 0)
      const tp = city.teletextPage
      if (tp) {
        buf = writeString(buf, 30, row, `P${tp}`, 3, 0)
      }
    })

    // Footer
    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, `CEETEX ${pageNum}  ${regionName}  ${new Date().toLocaleDateString('en-GB', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })}`, 7, 1)

    return { meta: { pageNumber: pageNum, title: regionName }, buffer: buf }
  }

  // ─── P350: Location status page ──────────────────────────────────

  private buildLocationPage(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    const loc = locationStore.getState()

    // Header
    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 350', 7, 4)
    buf = writeString(buf, 28, 0, 'P350', 7, 4)

    // Title
    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║      CURRENT LOCATION       ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    // Location info
    buf = writeString(buf, 4, 6, 'Location:', 2, 0, true)
    buf = writeString(buf, 18, 6, loc.locationName, 7, 0)

    buf = writeString(buf, 4, 8, 'uCode:', 2, 0, true)
    buf = writeString(buf, 18, 8, loc.uCode, 7, 0)

    buf = writeString(buf, 4, 10, 'GPS:', 2, 0, true)
    buf = writeString(buf, 18, 10, `${loc.lat.toFixed(4)}, ${loc.lon.toFixed(4)}`, 7, 0)

    buf = writeString(buf, 4, 12, 'Zoom Level:', 2, 0, true)
    buf = writeString(buf, 18, 12, `L${loc.level}`, 7, 0)

    buf = writeString(buf, 4, 14, 'Layer:', 2, 0, true)
    buf = writeString(buf, 18, 14, `${loc.layer}`, 7, 0)

    // Navigation hints
    buf = writeString(buf, 4, 16, 'NAVIGATION', 2, 0, true)
    buf = writeString(buf, 4, 17, 'Use terminal commands to navigate:', 7, 0)
    buf = writeString(buf, 4, 18, '  GOTO <city>    — Jump to a city', 7, 0)
    buf = writeString(buf, 4, 19, '  GPS <lat> <lon> — Jump to coordinates', 7, 0)
    buf = writeString(buf, 4, 20, '  N/S/E/W        — Move in a direction', 7, 0)
    buf = writeString(buf, 4, 21, '  ZOOM IN/OUT    — Change zoom level', 7, 0)
    buf = writeString(buf, 4, 22, '  WHERE          — Show current location', 7, 0)

    // Footer
    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, `CEETEX 350  Current Location  ${new Date().toLocaleDateString('en-GB', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })}`, 7, 1)

    return { meta: { pageNumber: 350, title: 'Current Location' }, buffer: buf }
  }

  private buildColourTestCard(): TeletextPage {
    let buf = createBuffer(PAGE_COLS, PAGE_ROWS)

    buf = fill(buf, 0, 0, 40, 1, ' ', 7, 4)
    buf = writeString(buf, 2, 0, 'CEETEX 888', 7, 4)
    buf = writeString(buf, 28, 0, 'P888', 7, 4)

    buf = writeString(buf, 4, 2, '╔══════════════════════════════╗', 3, 0, true)
    buf = writeString(buf, 4, 3, '║     COLOUR TEST CARD        ║', 3, 0, true)
    buf = writeString(buf, 4, 4, '╚══════════════════════════════╝', 3, 0, true)

    // Colour bars (rows 6-10)
    const colours = [
      { fg: 0, bg: 0, label: 'BLACK' },
      { fg: 1, bg: 1, label: 'RED' },
      { fg: 2, bg: 2, label: 'GREEN' },
      { fg: 3, bg: 3, label: 'YELLOW' },
      { fg: 4, bg: 4, label: 'BLUE' },
      { fg: 5, bg: 5, label: 'MAGENTA' },
      { fg: 6, bg: 6, label: 'CYAN' },
      { fg: 7, bg: 7, label: 'WHITE' },
    ]

    colours.forEach((c, i) => {
      const x = i * 5
      buf = fill(buf, x, 6, 5, 1, ' ', 7, c.bg)
      buf = writeString(buf, x, 6, c.label, c.fg === 0 ? 7 : c.fg, c.bg)
    })

    // Bright colours (rows 8-10)
    const brightColours = [
      { fg: 8, bg: 8, label: 'BR-BLK' },
      { fg: 9, bg: 9, label: 'BR-RED' },
      { fg: 10, bg: 10, label: 'BR-GRN' },
      { fg: 11, bg: 11, label: 'BR-YEL' },
      { fg: 12, bg: 12, label: 'BR-BLU' },
      { fg: 13, bg: 13, label: 'BR-MAG' },
      { fg: 14, bg: 14, label: 'BR-CYN' },
      { fg: 15, bg: 15, label: 'BR-WHT' },
    ]

    brightColours.forEach((c, i) => {
      const x = i * 5
      buf = fill(buf, x, 8, 5, 1, ' ', 7, c.bg)
      buf = writeString(buf, x, 8, c.label, c.fg === 0 ? 7 : c.fg, c.bg)
    })

    buf = writeString(buf, 4, 12, 'All 16 colours displayed above.', 7, 0)
    buf = writeString(buf, 4, 13, 'Colours 0-7 are standard ANSI.', 7, 0)
    buf = writeString(buf, 4, 14, 'Colours 8-15 are bright variants.', 7, 0)

    buf = writeString(buf, 4, 16, 'Palette: Unified Dark', 2, 0, true)
    buf = writeString(buf, 4, 17, '(Bootstrap / GitHub Dark)', 7, 0)

    buf = fill(buf, 0, 24, 40, 1, ' ', 7, 1)
    buf = writeString(buf, 2, 24, 'CEETEX 888  Colour Test Card  Mon 11 Jun 2026  00:00:00', 7, 1)

    return { meta: { pageNumber: 888, title: 'Colour Test Card' }, buffer: buf }
  }
}
