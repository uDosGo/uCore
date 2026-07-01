/* ═══════════════════════════════════════════════════════════════════
   SurfacesPanel — Developer Surface Ecosystem Browser
   Lists all canonical surfaces (routes), S-pages, and orphaned
   surfaces discovered via the backend Surface Manager API.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { Icon } from '../../components/Icon'

interface SurfaceEntry {
  id: string
  name: string
  route: string
  type: 'canonical' | 's-page' | 'backend' | 'orphan'
  status?: string
  description?: string
  icon?: string
  color?: string
  state?: string
  surface_id?: string
}

const SNACKBAR_API = 'http://localhost:8484'

/* Canonical surfaces from main.tsx route table */
const CANONICAL_SURFACES: SurfaceEntry[] = [
  { id: 'workflow', name: 'Workflow', route: '/workflow', type: 'canonical', icon: 'checklist', color: '#3fb950', description: 'Daily missions, tasks, activity' },
  { id: 'terminal', name: 'Terminal', route: '/terminal', type: 'canonical', icon: 'terminal', color: '#58a6ff', description: 'BBC BASIC terminal' },
  { id: 'teletext', name: 'Teletext', route: '/teletext', type: 'canonical', icon: 'tv', color: '#d29922', description: 'Ceefax page viewer' },
  { id: 'ucode', name: 'uCode', route: '/ucode', type: 'canonical', icon: 'grid_view', color: '#39d2c0', description: 'GridCore toolset dashboard' },
  { id: 'browserui', name: 'Browser UI', route: '/browserui', type: 'canonical', icon: 'language', color: '#d29922', description: 'Web reader / bookmark browser' },
  { id: 'assistui', name: 'Assist UI', route: '/assistui', type: 'canonical', icon: 'smart_toy', color: '#a371f7', description: 'Canonical AI chat interface' },
  { id: 'documentation', name: 'Documentation', route: '/documentation', type: 'canonical', icon: 'menu_book', color: '#22c55e', description: 'Learning hub, courses, docs' },
  { id: 'developer', name: 'Developer', route: '/developer', type: 'canonical', icon: 'code', color: '#f0883e', description: 'Dev Studio (gated by DevMode)' },
  { id: 'server', name: 'uServer', route: '/server', type: 'canonical', icon: 'dns', color: '#2f81f7', description: 'Backend operations' },
  { id: 'system', name: 'uSystem', route: '/system', type: 'canonical', icon: 'tune', color: '#bc8cff', description: 'Admin config, settings, variables' },
  { id: 'dashboard', name: 'Dashboard', route: '/', type: 'canonical', icon: 'dashboard', color: '#f2cc60', description: 'Surface hub overview' },
  { id: 'gridui', name: 'GridUI (Legacy)', route: '/gridui', type: 'orphan', icon: 'grid_view', color: '#8b949e', description: 'Redirected to /terminal' },
  { id: 'userver', name: 'uServer Legacy', route: '/userver', type: 'orphan', icon: 'backup', color: '#8b949e', description: 'Redirected to /server' },
]

/* S-pages from spage-registry */
const S_PAGES: SurfaceEntry[] = [
  { id: 's100', name: 'Tool Builder', route: '/s100', type: 's-page', icon: 'build', color: '#58a6ff' },
  { id: 's101', name: 'Story Builder', route: '/s101', type: 's-page', icon: 'auto_stories', color: '#a371f7' },
  { id: 's300', name: 'Workflow Builder', route: '/s300', type: 's-page', icon: 'account_tree', color: '#3fb950' },
  { id: 's310', name: 'Clipboard Orchestration', route: '/s310', type: 's-page', icon: 'content_paste', color: '#d29922' },
  { id: 's320', name: 'Knowledge Tools', route: '/s320', type: 's-page', icon: 'lightbulb', color: '#22c55e' },
  { id: 's330', name: 'Migration Dashboard', route: '/s330', type: 's-page', icon: 'sync', color: '#f0883e' },
  { id: 's600', name: 'Learning', route: '/s600', type: 's-page', icon: 'school', color: '#bc8cff' },
]

export function SurfacesPanel() {
  const [backendSurfaces, setBackendSurfaces] = useState<SurfaceEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedSection, setExpandedSection] = useState<string | null>('canonical')

  useEffect(() => {
    async function fetchBackendSurfaces() {
      try {
        const res = await fetch(`${SNACKBAR_API}/api/surfaces`, {
          signal: AbortSignal.timeout(3000),
        })
        if (!res.ok) throw new Error('Backend surfaces unavailable')
        const data = await res.json()
        const backendMapped: SurfaceEntry[] = (data.surfaces || []).map((s: any) => ({
          id: s.id || s.name || 'unknown',
          name: s.name || s.id || 'Unnamed',
          route: s.route || '',
          type: 'backend' as const,
          status: s.status || s.state || 'unknown',
          icon: 'widgets',
          color: '#58a6ff',
          state: s.state,
          surface_id: s.id,
          description: `Type: ${s.type || 'unknown'} · State: ${s.state || 'unknown'}`,
        }))
        setBackendSurfaces(backendMapped)
      } catch (err: any) {
        setError(err?.message || 'Failed to fetch backend surfaces')
      } finally {
        setLoading(false)
      }
    }
    void fetchBackendSurfaces()
  }, [])

  const toggleSection = (sectionId: string) => {
    setExpandedSection(prev => prev === sectionId ? null : sectionId)
  }

  const statusColor = (state?: string) => {
    switch (state) {
      case 'running': return '#3fb950'
      case 'stopped': return '#8b949e'
      case 'error': return '#f85149'
      default: return 'var(--pico-muted-color, #8b949e)'
    }
  }

  const sections = [
    {
      id: 'canonical',
      label: 'Canonical Surfaces',
      icon: 'apps',
      count: CANONICAL_SURFACES.length,
      items: CANONICAL_SURFACES,
      empty: false,
    },
    {
      id: 's-pages',
      label: 'S-Pages',
      icon: 'description',
      count: S_PAGES.length,
      items: S_PAGES,
      empty: false,
    },
    {
      id: 'backend',
      label: 'Backend Surfaces',
      icon: 'cloud',
      count: backendSurfaces.length,
      items: backendSurfaces,
      empty: !loading && backendSurfaces.length === 0,
    },
  ]

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">
          <Icon name="dashboard" size={16} /> Surface Ecosystem
        </h3>
        <span className="developer-panel-count">
          {CANONICAL_SURFACES.length + S_PAGES.length + backendSurfaces.length} total
        </span>
      </div>

      {error && (
        <div style={{
          padding: '8px 12px',
          background: 'rgba(210,153,34,0.1)',
          color: '#d29922',
          borderRadius: 6,
          fontSize: 12,
          marginBottom: 8,
        }}>
          <Icon name="warning" size={14} /> {error}
        </div>
      )}

      {loading && (
        <div className="developer-panel-count">Loading backend surfaces...</div>
      )}

      {sections.map(section => (
        <div key={section.id} className="developer-settings-section" style={{ padding: 0, overflow: 'hidden' }}>
          <button
            onClick={() => toggleSection(section.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '12px 14px',
              width: '100%',
              border: 'none',
              background: 'transparent',
              color: 'var(--pico-color, #c9d1d9)',
              cursor: 'pointer',
              fontFamily: 'inherit',
              fontSize: 13,
              fontWeight: 600,
              borderBottom: expandedSection === section.id ? '1px solid var(--pico-border-color, #30363d)' : 'none',
            }}
          >
            <Icon name={section.icon as any} size={16} />
            <span style={{ flex: 1, textAlign: 'left' }}>{section.label}</span>
            <span className="developer-panel-count">{section.count}</span>
            <Icon name={expandedSection === section.id ? 'expand_less' : 'expand_more'} size={16} />
          </button>

          {expandedSection === section.id && (
            <div style={{ padding: '8px 14px 12px' }}>
              {section.empty ? (
                <div className="developer-panel-count">
                  {section.id === 'backend' ? 'No backend surfaces discovered' : 'No surfaces'}
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {(section.items as SurfaceEntry[]).map(surface => (
                    <div
                      key={surface.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '8px 10px',
                        borderRadius: 6,
                        background: 'var(--pico-card-background-color, #161b22)',
                        border: '1px solid var(--pico-border-color, #30363d)',
                        cursor: 'default',
                      }}
                    >
                      <span style={{
                        width: 28,
                        height: 28,
                        borderRadius: 6,
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: `${surface.color || '#58a6ff'}20`,
                        color: surface.color || '#58a6ff',
                        flexShrink: 0,
                      }}>
                        <Icon name={(surface.icon || 'widgets') as any} size={16} />
                      </span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{
                          fontWeight: 600,
                          color: 'var(--pico-color, #c9d1d9)',
                          fontSize: 13,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}>
                          {surface.name}
                          <span style={{
                            fontSize: 10,
                            color: 'var(--pico-muted-color, #8b949e)',
                            background: 'var(--pico-card-sectioning-background-color, #1c2128)',
                            padding: '1px 6px',
                            borderRadius: 4,
                          }}>
                            {surface.type}
                          </span>
                        </div>
                        <div style={{
                          fontSize: 11,
                          color: 'var(--pico-muted-color, #8b949e)',
                          fontFamily: 'monospace',
                        }}>
                          {surface.route || surface.id}
                          {surface.state && (
                            <span style={{ marginLeft: 8, color: statusColor(surface.state) }}>
                              · {surface.state}
                            </span>
                          )}
                        </div>
                        {surface.description && (
                          <div style={{ fontSize: 11, color: 'var(--pico-muted-color, #8b949e)', marginTop: 2 }}>
                            {surface.description}
                          </div>
                        )}
                      </div>
                      <a
                        href={surface.route || `/${surface.id}`}
                        className="developer-repo-btn"
                        style={{ textDecoration: 'none', fontSize: 11, padding: '4px 8px', flexShrink: 0 }}
                      >
                        <Icon name="open_in_new" size={12} /> Open
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ))}

      {/* Legend */}
      <div style={{
        display: 'flex',
        gap: 12,
        flexWrap: 'wrap',
        fontSize: 11,
        color: 'var(--pico-muted-color, #8b949e)',
        padding: '8px 0',
      }}>
        <span><span style={{ color: '#58a6ff', fontWeight: 600 }}>●</span> canonical — Route-registered surface</span>
        <span><span style={{ color: '#a371f7', fontWeight: 600 }}>●</span> s-page — S-Page tool (S100-S899)</span>
        <span><span style={{ color: '#d29922', fontWeight: 600 }}>●</span> backend — From Backend API</span>
        <span><span style={{ color: '#8b949e', fontWeight: 600 }}>●</span> orphan — Legacy/redirected</span>
      </div>
    </div>
  )
}