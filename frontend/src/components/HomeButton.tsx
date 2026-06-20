/* ═══════════════════════════════════════════════════════════════════
   HomeButton — Persistent home button (top-left) on all surfaces
   ═══════════════════════════════════════════════════════════════════
   Uses React Router's useNavigate to go back to the card grid.
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { useNavigate } from 'react-router-dom'

export function HomeButton() {
  const navigate = useNavigate()

  return (
    <button
      className="surface-home-button"
      onClick={() => navigate('/')}
      title="Back to UI Hub"
      aria-label="Home"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
    </button>
  )
}
