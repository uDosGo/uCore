/* ═══════════════════════════════════════════════════════════════════
   uSystemPage — USX Standard v2 System Page Wrapper
   ═══════════════════════════════════════════════════════════════════
   Provides consistent layout, theming, and navigation for all
   S100–S899 system pages. Uses Pico.css data-theme for theming.
   
   Theme mapping:
     S100–S299: core (blue)
     S300–S399: media (blue)
     S400–S499: automation (green)
     S500–S599: development (orange)
     S600–S699: learning (purple)
     S700–S799: labs (cyan)
     S800–S899: fallback (red)
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { Icon } from './Icon'
import '../styles/nestframe.css'

// ─── Theme Mapping ──────────────────────────────────────────────────
const THEME_MAP: Record<string, string> = {
  core: 'blue',
  media: 'blue',
  automation: 'green',
  development: 'orange',
  learning: 'purple',
  labs: 'cyan',
  fallback: 'red',
}

const PAGE_THEME: Record<string, string> = {}
for (let i = 100; i < 300; i++) PAGE_THEME[`s${i}`] = 'core'
for (let i = 300; i < 400; i++) PAGE_THEME[`s${i}`] = 'media'
for (let i = 400; i < 500; i++) PAGE_THEME[`s${i}`] = 'automation'
for (let i = 500; i < 600; i++) PAGE_THEME[`s${i}`] = 'development'
for (let i = 600; i < 700; i++) PAGE_THEME[`s${i}`] = 'learning'
for (let i = 700; i < 800; i++) PAGE_THEME[`s${i}`] = 'labs'
for (let i = 800; i < 900; i++) PAGE_THEME[`s${i}`] = 'fallback'

function getThemeForPage(page: number): string {
  const key = `s${page}`
  return THEME_MAP[PAGE_THEME[key] || 'core'] || 'blue'
}

// ─── Props ──────────────────────────────────────────────────────────
interface USystemPageProps {
  page: number
  title: string
  subtitle?: string
  theme?: string
  children: React.ReactNode
  headerExtra?: React.ReactNode
  footerText?: string
}

// ─── Component ──────────────────────────────────────────────────────
export default function USystemPage({
  page,
  title,
  subtitle,
  theme,
  children,
  headerExtra,
  footerText,
}: USystemPageProps) {
  const picoTheme = theme || getThemeForPage(page)
  const pageCode = `S${page}`

  return (
    <div data-theme={picoTheme} className="uSystem-page">
      <header className="uSystem-page-header">
        <hgroup>
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </hgroup>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {headerExtra}
          <span className="uSystem-page-badge">
            <Icon name="code" size={12} />
            {pageCode}
          </span>
        </div>
      </header>

      <div className="uSystem-page-body">
        {children}
      </div>

      <footer className="uSystem-page-footer">
        {footerText || `${pageCode} · uDosConnect`}
      </footer>
    </div>
  )
}
