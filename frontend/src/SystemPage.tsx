/* ═══════════════════════════════════════════════════════════════════
   SystemPage — uDos System Pages (P100-P899 + S100-S899)
   ═══════════════════════════════════════════════════════════════════
   Unified system/fallback pages served by the UI Hub itself.
   P-pages: Surface status/error pages (legacy)
   S-pages: System pages (S100-S899, fallbacks S100-S190)
   Uses USX Icon component for consistent iconography with GlobalToolbar.
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { Icon } from './components/Icon'
import { GlobalToolbar } from './components/GlobalToolbar'
import SystemPageFallback from './pages/SystemPageFallback'
import './styles/hub/index.css'
import './styles/global-toolbar.css'


// ─── Page Registry ─────────────────────────────────────────────────
interface PageDef {
  code: string
  title: string
  icon: string
  color: string
  description: string
}

const PAGE_REGISTRY: Record<string, PageDef> = {
  // ─── P-pages (Surface status/error — legacy) ───────────────────
  p100: { code: 'P100', title: 'System Boot', icon: 'forum', color: '#00ff9d', description: 'Initialising system services...' },
  p200: { code: 'P200', title: 'Surface Ready', icon: 'forum', color: '#3fb950', description: 'Surface is online and ready.' },
  p800: { code: 'P800', title: 'Surface Not Found', icon: 'forum', color: '#f0883e', description: 'The requested surface could not be located.' },
  p801: { code: 'P801', title: 'Starting Surface', icon: 'forum', color: '#58a6ff', description: 'Surface is starting up \u2014 please wait...' },
  p802: { code: 'P802', title: 'Surface Offline', icon: 'forum', color: '#f97583', description: 'Surface is offline or unreachable.' },
  p804: { code: 'P804', title: 'Surface Unavailable', icon: 'forum', color: '#f85149', description: 'This surface is not available. It may be offline or not installed.' },
  p805: { code: 'P805', title: 'Service Error', icon: 'forum', color: '#d29922', description: 'A service error occurred while loading this surface.' },
  p810: { code: 'P810', title: 'Port Conflict', icon: 'forum', color: '#da3633', description: 'Multiple processes detected on the same port.' },
  p820: { code: 'P820', title: 'Maintenance Mode', icon: 'forum', color: '#f0883e', description: 'This surface is undergoing maintenance.' },
  p822: { code: 'P822', title: 'Updating Surface', icon: 'forum', color: '#58a6ff', description: 'Surface is being updated \u2014 please wait...' },
  p830: { code: 'P830', title: 'Configuration Error', icon: 'forum', color: '#f97583', description: 'Surface configuration is invalid or incomplete.' },
  p890: { code: 'P890', title: 'Diagnostics', icon: 'forum', color: '#3fb950', description: 'Running system diagnostics...' },
  p900: { code: 'P900', title: 'DNS Resolution Failed', icon: 'forum', color: '#f85149', description: 'Could not resolve the surface address.' },
  p904: { code: 'P904', title: 'Gateway Timeout', icon: 'forum', color: '#d29922', description: 'The surface did not respond in time.' },
  p910: { code: 'P910', title: 'Rate Limited', icon: 'forum', color: '#da3633', description: 'Too many requests \u2014 please wait before retrying.' },
  p950: { code: 'P950', title: 'Surface Console', icon: 'forum', color: '#00ff9d', description: 'Surface management console overlay.' },
  p999: { code: 'P999', title: 'Unknown Error', icon: 'forum', color: '#f85149', description: 'An unknown error occurred.' },

  // ─── S-pages (System pages — S100-S899, fallbacks S100-S190) ───
  s100: { code: 'S100', title: 'Tool Builder', icon: 'build', color: '#58a6ff', description: 'Create and manage system tools.' },
  s101: { code: 'S101', title: 'Story Builder', icon: 'auto_stories', color: '#58a6ff', description: 'Create and manage interactive stories.' },
  s110: { code: 'S110', title: 'System Boot', icon: 'power', color: '#00ff9d', description: 'System boot sequence and startup services.' },
  s120: { code: 'S120', title: 'System Config', icon: 'tune', color: '#f0883e', description: 'System configuration and environment settings.' },
  s130: { code: 'S130', title: 'System Status', icon: 'monitor_heart', color: '#3fb950', description: 'System health and status overview.' },
  s140: { code: 'S140', title: 'System Logs', icon: 'history', color: '#8b949e', description: 'System log viewer and diagnostics.' },
  s150: { code: 'S150', title: 'System Network', icon: 'network_check', color: '#58a6ff', description: 'Network configuration and connectivity.' },
  s160: { code: 'S160', title: 'System Security', icon: 'lock', color: '#f85149', description: 'Security settings and access control.' },
  s170: { code: 'S170', title: 'System Storage', icon: 'storage', color: '#d29922', description: 'Storage management and disk usage.' },
  s180: { code: 'S180', title: 'System Updates', icon: 'system_update', color: '#58a6ff', description: 'System update management.' },
  s190: { code: 'S190', title: 'System Fallback', icon: 'warning', color: '#f0883e', description: 'Fallback system page.' },
  s200: { code: 'S200', title: 'Health Dashboard', icon: 'monitor_heart', color: '#3fb950', description: 'System health monitoring dashboard.' },
  s300: { code: 'S300', title: 'Workflow Builder', icon: 'account_tree', color: '#58a6ff', description: 'Design and manage automated workflows.' },
  s310: { code: 'S310', title: 'Clipboard & Orchestration', icon: 'content_paste', color: '#22c55e', description: 'System clipboard buffer and overnight maintenance chain.' },
  s320: { code: 'S320', title: 'Knowledge Tools', icon: 'auto_stories', color: '#a855f7', description: 'AppFlowy workspace browser, document viewer, and semantic search.' },
  s400: { code: 'S400', title: 'Maintenance', icon: 'build', color: '#f0883e', description: 'System maintenance and repair tools.' },
  s500: { code: 'S500', title: 'Log Viewer', icon: 'history', color: '#8b949e', description: 'System log viewer and analysis.' },
  s600: { code: 'S600', title: 'Learning Hub', icon: 'school', color: '#a855f7', description: 'Tutorials, guides, and educational resources.' },
  s700: { code: 'S700', title: 'Security', icon: 'lock', color: '#f85149', description: 'Security settings and audit logs.' },
  s899: { code: 'S899', title: 'System Console', icon: 'terminal', color: '#00ff9d', description: 'System management console overlay.' },
}



// ─── Props ─────────────────────────────────────────────────────────
interface SystemPageProps {
  pageCode: string
  surface?: {
    name?: string
    port?: number
    id?: string
    color?: string
    icon?: string
  }
  error?: string
}

// ─── System Page Toolbar ───────────────────────────────────────────
function SystemPageToolbar({ currentCode }: { currentCode: string }) {
  const sysLinks = [
    { code: 's100', icon: 'build', label: 'Tool Builder' },
    { code: 's101', icon: 'auto_stories', label: 'Story Builder' },
    { code: 's300', icon: 'account_tree', label: 'Workflows' },
    { code: 's310', icon: 'content_paste', label: 'Clipboard' },
    { code: 's320', icon: 'auto_stories', label: 'Knowledge' },
    { code: 's600', icon: 'school', label: 'Learning' },
  ]

  return (
    <header className="usx-surface-header global-toolbar sys-page-toolbar">
      <div className="usx-header-left">
        <button
          className="usx-header-btn"
          onClick={() => window.location.href = '/'}
          title="Back to UI Hub"
          aria-label="Home"
        >
          <Icon name="home" size={18} />
        </button>
      </div>

      <nav className="global-toolbar-nav">
        {sysLinks.map(link => (
          <a
            key={link.code}
            href={`/${link.code}`}
            className={`global-toolbar-nav-btn ${currentCode === link.code ? 'active' : ''}`}
            title={link.label}
          >
            <Icon name={link.icon} size={16} />
            <span>{link.label}</span>
          </a>
        ))}
      </nav>

      <div className="usx-header-right">
        {/* System page toolbar only shows home on left and nav in center — no duplicate right-side buttons */}
      </div>
    </header>
  )
}

// ─── System Page Component ─────────────────────────────────────────
export function SystemPage({ pageCode, surface, error }: SystemPageProps) {
  // For unmapped S-pages, use the fallback component
  if (pageCode.toLowerCase().startsWith('s') && !PAGE_REGISTRY[pageCode.toLowerCase()]) {
    return <SystemPageFallback pageCode={pageCode} />
  }

  const code = pageCode.toLowerCase().replace(/[^ps0-9]/g, '')
  const page = PAGE_REGISTRY[code] || PAGE_REGISTRY['p999']
  const accentColor = surface?.color || page.color
  const surfaceName = surface?.name || 'Unknown Surface'
  const port = surface?.port

  const isOffline = ['p800', 'p802', 'p804', 'p805', 'p830', 'p900', 'p904', 'p910', 'p999'].includes(code)
  const isStarting = ['p100', 'p801', 'p822', 'p890'].includes(code)
  const isSystemPage = code.startsWith('s')

  return (
    <div className={`sys-page ${isSystemPage ? 'sys-page--system' : ''}`} style={{ '--sys-accent': accentColor } as React.CSSProperties}>
      {isSystemPage && <SystemPageToolbar currentCode={code} />}

      <div className="sys-page-container">
        {isStarting && (
          <div className="sys-page-loader" style={{ borderTopColor: accentColor }} />
        )}

        {/* ─── USX Icon — hidden when status/alert icon is shown ─── */}
        {!isOffline && !isStarting && (
          <div className="sys-page-icon">
            <Icon name={page.icon} size={40} />
          </div>
        )}

        {isOffline && (
          <div className="sys-page-status-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke={accentColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
        )}

        <h1 className="sys-page-title">{page.title}</h1>

        <span className="sys-page-badge" style={{ background: `${accentColor}20`, color: accentColor, borderColor: `${accentColor}40` }}>
          {page.code}
        </span>
        
        <p className="sys-page-desc">{error || page.description}</p>

        {port && (
          <div className="sys-page-meta">
            <span className="sys-page-tag">{surfaceName}</span>
            <span className="sys-page-tag">:{port}</span>
          </div>
        )}

        <div className="sys-page-actions">
          <button className="sys-btn sys-btn--primary" onClick={() => window.location.href = '/'}>
            Back to UI Hub
          </button>
          {port && (
            <button className="sys-btn sys-btn--secondary" onClick={() => { window.location.reload() }}>
              Retry
            </button>
          )}
        </div>
      </div>

      <div className="sys-page-footer">
        <kbd>{page.code}</kbd>
        <kbd>uDosConnect</kbd>
      </div>
    </div>
  )
}

// ─── Parse route from window.location.pathname ─────────────────────
export function parseSystemRoute(path: string): SystemPageProps | null {
  // Match both P-pages (p100-p999) and S-pages (s100-s899)
  const match = path.match(/^\/([ps]\d{3,4})(?:\/([^/?]+))?(?:\?(.+))?$/i)
  if (!match) return null

  const pageCode = match[1].toLowerCase()
  const surfaceId = match[2]
  const params = new URLSearchParams(match[3] || '')

  // Parse surface info from params
  const surfaceName = params.get('name') || surfaceId
  const portStr = params.get('port')
  
  const surface = (surfaceName || portStr) ? {
    id: surfaceId || params.get('surface') || undefined,
    name: surfaceName || undefined,
    port: portStr ? parseInt(portStr) : undefined,
  } : undefined

  return {
    pageCode,
    error: params.get('error') || undefined,
    surface: surface as any,
  }
}
