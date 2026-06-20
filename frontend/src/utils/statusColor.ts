/* ═══════════════════════════════════════════════════════════════════
   statusColor — Shared utility for mapping status/priority to colors
   ═══════════════════════════════════════════════════════════════════ */

export function statusColor(status: string): string {
  switch (status) {
    case 'active': return '#238636'
    case 'completed': return '#58a6ff'
    case 'paused': return '#d29922'
    case 'planned': return '#8b949e'
    case 'cancelled': return '#f85149'
    case 'critical': return '#f85149'
    case 'high': return '#d29922'
    case 'medium': return '#58a6ff'
    case 'low': return '#8b949e'
    case 'draft': return '#94a3b8'
    case 'review': return '#f59e0b'
    case 'published': return '#22c55e'
    default: return '#8b949e'
  }
}
