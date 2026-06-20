/* ═══════════════════════════════════════════════════════════════════
   SurfaceToolbar — Viewport dropdown and nav keypad
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { useStore } from '../GridUIStore'

// ─── Viewport Dropdown ──────────────────────────────────────────────
export function ViewportDropdown() {
  const store = useStore()
  const [open, setOpen] = React.useState(false)
  const ref = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const presets = [
    { label: '40×25', cols: 40, rows: 25 },
    { label: '80×24', cols: 80, rows: 24 },
    { label: '60×24', cols: 60, rows: 24 },
    { label: '40×24', cols: 40, rows: 24 },
    { label: '80×48', cols: 80, rows: 48 },
    { label: '120×36', cols: 120, rows: 36 },
  ]

  return (
    <div ref={ref} style={{ position: 'absolute', bottom: 8, right: 8, zIndex: 50 }}>
      <button onClick={() => setOpen(v => !v)} className="gridui-btn gridui-btn--small" style={{ background: 'var(--pico-card-background-color, #161b22)', backdropFilter: 'blur(8px)' }}>
        {store.viewport.cols}×{store.viewport.rows} ▾
      </button>
      {open && (
        <div style={{ position: 'absolute', bottom: '100%', right: 0, marginBottom: 4, background: 'var(--pico-card-background-color, #161b22)', border: '1px solid var(--pico-border-color, #30363d)', borderRadius: 6, overflow: 'hidden', minWidth: 120, boxShadow: '0 4px 12px rgba(0,0,0,0.4)' }}>
          {presets.map(p => (
            <button key={p.label} onClick={() => { store.setViewport({ cols: p.cols, rows: p.rows }); setOpen(false) }}
              style={{ display: 'block', width: '100%', padding: '6px 12px', border: 'none', background: store.viewport.cols === p.cols && store.viewport.rows === p.rows ? 'var(--pico-card-sectioning-background-color, #1c2128)' : 'transparent', color: 'var(--pico-color, #c9d1d9)', cursor: 'pointer', fontFamily: 'inherit', fontSize: 12, textAlign: 'left' }}>
              {p.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Nav Keypad ─────────────────────────────────────────────────────
export function NavKeypad() {
  const store = useStore()

  const navStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 2,
    padding: 8,
    background: 'var(--pico-card-background-color, #161b22)',
    border: '1px solid var(--pico-border-color, #30363d)',
    borderRadius: 8,
  }

  const btnStyle: React.CSSProperties = {
    width: 28,
    height: 28,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '1px solid var(--pico-border-color, #30363d)',
    borderRadius: 4,
    background: 'transparent',
    color: 'var(--grid-text-secondary, #8b949e)',
    cursor: 'pointer',
    fontFamily: 'inherit',
    fontSize: 12,
  }

  return (
    <div style={navStyle}>
      <div style={{ display: 'flex', gap: 2 }}>
        <button style={btnStyle} onClick={() => store.setViewport({ cols: store.viewport.cols + 1 })} title="Increase width">→</button>
      </div>
      <div style={{ display: 'flex', gap: 2 }}>
        <button style={btnStyle} onClick={() => store.setViewport({ cols: Math.max(24, store.viewport.cols - 1) })} title="Decrease width">←</button>
        <button style={{ ...btnStyle, background: 'var(--pico-card-sectioning-background-color, #1c2128)', color: 'var(--pico-color, #c9d1d9)' }} onClick={() => store.setViewport({ cols: 80, rows: 24 })} title="Reset">⌂</button>
        <button style={btnStyle} onClick={() => store.setViewport({ cols: store.viewport.cols + 1 })} title="Increase width">→</button>
      </div>
      <div style={{ display: 'flex', gap: 2 }}>
        <button style={btnStyle} onClick={() => store.setViewport({ rows: Math.max(4, store.viewport.rows - 1) })} title="Decrease height">↑</button>
      </div>
    </div>
  )
}

// ─── Legacy alias for TerminalPanel ─────────────────────────────────
export const SurfaceToolbar = ViewportDropdown
