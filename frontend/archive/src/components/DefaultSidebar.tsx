/**
 * DefaultSidebar — Minimal file picker sidebar
 * Appears inline under the GlobalToolbar on surfaces that don't have
 * their own dedicated sidebar (e.g. browserui, assistui)
 */
import React from 'react'

export interface DefaultSidebarProps {
  open?: boolean
}

export const DefaultSidebar: React.FC<DefaultSidebarProps> = ({ open = true }) => {
  if (!open) return null

  return (
    <div className="default-sidebar" style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--usx-spacing-md)',
      padding: 'var(--usx-spacing-sm) var(--usx-spacing-lg)',
      borderBottom: '1px solid var(--pico-border-color)',
      backgroundColor: 'var(--pico-card-background-color)',
      fontSize: '0.95rem',
      color: 'var(--pico-muted-color)',
    }}>
      {/* Placeholder: FileTree/FilePicker goes here */}
      <span>Files</span>
    </div>
  )
}

export default DefaultSidebar
