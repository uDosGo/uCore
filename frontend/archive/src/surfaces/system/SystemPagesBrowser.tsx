/* ═══════════════════════════════════════════════════════════════════
   SystemPagesBrowser — Browsable System Pages (routes/status/fallbacks)
   ═══════════════════════════════════════════════════════════════════
   Things that are routes, status pages, fallbacks, or notifications.
   Things that DO something go in the Tools tab instead.
   Uses only Pico CSS classes — no inline font-size or color hacks.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon } from '../../components/Icon'
import './system-surface.css'

interface SysPageEntry {
  code: string
  name: string
  description: string
  icon: string
  category: string
  route: string
  status: 'built' | 'stub' | 'planned'
}

const ALL_SYSTEM_PAGES: SysPageEntry[] = [
  { code: 'S110', name: 'System Boot', description: 'System boot sequence and startup services', icon: 'power', category: 'status', route: '/s110', status: 'stub' },
  { code: 'S120', name: 'System Config', description: 'System configuration and environment settings', icon: 'tune', category: 'config', route: '/s120', status: 'stub' },
  { code: 'S130', name: 'System Status', description: 'System health and status overview', icon: 'monitor_heart', category: 'status', route: '/s130', status: 'stub' },
  { code: 'S140', name: 'System Logs', description: 'System log viewer and diagnostics', icon: 'history', category: 'diagnostics', route: '/s140', status: 'stub' },
  { code: 'S150', name: 'System Network', description: 'Network configuration and connectivity', icon: 'network_check', category: 'config', route: '/s150', status: 'stub' },
  { code: 'S160', name: 'System Security', description: 'Security settings', icon: 'lock', category: 'config', route: '/s160', status: 'stub' },
  { code: 'S170', name: 'System Storage', description: 'Storage management and disk usage', icon: 'storage', category: 'status', route: '/s170', status: 'stub' },
  { code: 'S180', name: 'System Updates', description: 'System update management', icon: 'system_update', category: 'status', route: '/s180', status: 'stub' },
  { code: 'S200', name: 'Health Dashboard', description: 'System health monitoring', icon: 'monitor_heart', category: 'status', route: '/s200', status: 'stub' },
  { code: 'S400', name: 'Maintenance', description: 'System maintenance and repair tools', icon: 'build', category: 'status', route: '/s400', status: 'stub' },
  { code: 'S500', name: 'Log Viewer', description: 'Log viewer and analysis', icon: 'history', category: 'diagnostics', route: '/s500', status: 'stub' },
  { code: 'S600', name: 'Learning Hub', description: 'Tutorials, guides, educational resources', icon: 'school', category: 'learning', route: '/s600', status: 'built' },
  { code: 'S700', name: 'Security', description: 'Security settings and audit logs', icon: 'lock', category: 'config', route: '/s700', status: 'stub' },
  { code: 'S899', name: 'System Console', description: 'System management console overlay', icon: 'terminal', category: 'status', route: '/s899', status: 'stub' },
  { code: 'P100', name: 'System Boot Init', description: 'Initialising system services...', icon: 'power', category: 'fallback', route: '/p100', status: 'built' },
  { code: 'P200', name: 'Surface Ready', description: 'Surface is online and ready', icon: 'check_circle', category: 'fallback', route: '/p200', status: 'built' },
  { code: 'P800', name: 'Surface Not Found', description: 'The requested surface could not be located', icon: 'error', category: 'fallback', route: '/p800', status: 'built' },
  { code: 'P804', name: 'Surface Offline', description: 'Surface is unreachable', icon: 'cloud_off', category: 'fallback', route: '/p804', status: 'built' },
  { code: 'P999', name: 'Unknown Error', description: 'An unknown error occurred', icon: 'error', category: 'fallback', route: '/p999', status: 'built' },
]

const CATEGORIES = ['all', 'status', 'config', 'diagnostics', 'learning', 'fallback']

export default function SystemPagesBrowser() {
  const navigate = useNavigate()
  const [filterCategory, setFilterCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  const filteredPages = useMemo(() => {
    return ALL_SYSTEM_PAGES.filter(p => {
      if (filterCategory !== 'all' && p.category !== filterCategory) return false
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        return p.name.toLowerCase().includes(q) || p.code.toLowerCase().includes(q)
      }
      return true
    })
  }, [filterCategory, searchQuery])

  const builtCount = ALL_SYSTEM_PAGES.filter(p => p.status === 'built').length
  const stubCount = ALL_SYSTEM_PAGES.filter(p => p.status === 'stub').length

  return (
    <div className="system-panel">
      <div className="system-panel-header">
        <h3><Icon name="dashboard" size={16} /> System Pages</h3>
        <span className="system-panel-count">S100-S899</span>
      </div>
      <div className="system-stats">
        <div className="system-stat">
          <Icon name="check_circle" size={16} />
          <span className="system-stat-value">{builtCount}</span>
          <span>built</span>
        </div>
        <div className="system-stat">
          <Icon name="pending" size={16} />
          <span className="system-stat-value">{stubCount}</span>
          <span>stubs</span>
        </div>
      </div>

      <div className="system-filter-group">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            className={`system-filter-btn ${filterCategory === cat ? 'system-filter-btn--active' : ''}`}
            onClick={() => setFilterCategory(cat)}
          >
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
        <input
          type="search"
          className="system-search"
          placeholder="Search..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{ flex: 1, minWidth: '120px' }}
        />
      </div>

      {filteredPages.length === 0 ? (
        <div className="system-info-box">
          <p>No pages match your filter.</p>
        </div>
      ) : (
        <div className="system-card-grid">
          {filteredPages.map(page => (
            <div
              key={page.code}
              className="system-card"
              role="button"
              tabIndex={0}
              onClick={() => navigate(page.route)}
            >
              <div className="system-card-header">
                <div className="system-card-icon">
                  <Icon name={page.icon as any} size={20} />
                </div>
                <h5 className="system-card-title">{page.name}</h5>
              </div>
              <p className="system-card-desc">{page.description}</p>
              <div className="system-card-footer">
                <span className="system-card-code">{page.code}</span>
                <span className={`system-card-status ${page.status === 'built' ? '' : 'system-card-status--stub'}`}>
                  {page.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}