/* ═══════════════════════════════════════════════════════════════════
   formatRelativeTime — Shared utility for relative time formatting
   ═══════════════════════════════════════════════════════════════════ */

export function formatRelativeTime(dateString?: string): string {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
  const now = Date.now()
  const diff = now - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}
