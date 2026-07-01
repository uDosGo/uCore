import React, { useState, useEffect } from 'react'
import type { SnackbarMessage } from '../hooks/useSurfaceStore'

interface SurfaceSnackbarProps {
  snackbar: SnackbarMessage[]
  onDismiss: (id: string) => void
  maxVisible?: number
}

/**
 * SurfaceSnackbar — A floating snackbar/toast notification component.
 */
export const SurfaceSnackbar: React.FC<SurfaceSnackbarProps> = ({
  snackbar,
  onDismiss,
  maxVisible = 3,
}) => {
  const visible = snackbar.slice(0, maxVisible)
  if (visible.length === 0) return null

  return (
    <div className="usx-snackbar-container" style={containerStyle}>
      {visible.map(msg => (
        <SnackbarItem key={msg.id} message={msg} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

const SnackbarItem: React.FC<{ message: SnackbarMessage; onDismiss: (id: string) => void }> = ({
  message,
  onDismiss,
}) => {
  const [exiting, setExiting] = useState(false)

  useEffect(() => {
    const duration = message.duration ?? 4000
    if (duration > 0) {
      const timer = setTimeout(() => {
        setExiting(true)
        setTimeout(() => onDismiss(message.id), 300)
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [message.id, message.duration, onDismiss])

  const bgColor = typeColors[message.type ?? 'info'] ?? typeColors.info

  return (
    <div
      className={`usx-snackbar-item ${exiting ? 'usx-snackbar-exit' : ''}`}
      style={{
        ...itemStyle,
        background: bgColor,
        opacity: exiting ? 0 : 1,
        transform: exiting ? 'translateY(20px)' : 'translateY(0)',
        transition: 'opacity 0.3s ease, transform 0.3s ease',
      }}
    >
      <span style={{ flex: 1 }}>{message.message}</span>
      <button onClick={() => onDismiss(message.id)} style={closeBtnStyle} aria-label="Dismiss">
        ✕
      </button>
    </div>
  )
}

const typeColors: Record<string, string> = {
  info: '#1f6feb',
  success: '#238636',
  warning: '#d29922',
  error: '#da3633',
}

const containerStyle: React.CSSProperties = {
  position: 'fixed',
  bottom: 16,
  left: '50%',
  transform: 'translateX(-50%)',
  zIndex: 9999,
  display: 'flex',
  flexDirection: 'column',
  gap: 8,
  maxWidth: 480,
  width: '100%',
  pointerEvents: 'auto',
}

const itemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  padding: '8px 16px',
  borderRadius: 8,
  color: '#fff',
  fontSize: 14,
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
}

const closeBtnStyle: React.CSSProperties = {
  width: 24,
  height: 24,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  border: 'none',
  background: 'transparent',
  color: 'rgba(255,255,255,0.7)',
  cursor: 'pointer',
  fontSize: 14,
}
