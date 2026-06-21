/* ═══════════════════════════════════════════════════════════════════
   USystemSurface — System Tools Hub
   ═══════════════════════════════════════════════════════════════════
   Consolidates:
   - Install (app probes, Zen Browser mods)
   - Modules (installed system modules)
   - Feeds (feed source configuration & management)
   - Story Builder (step-by-step guides)
   - Pages (S100-S899 system page previews)
   ═══════════════════════════════════════════════════════════════════
   NOTE: Map, Grid, Assets, and Settings have been moved to
   GridCoreSurface (/gridcore/*) to keep grid-based CSS styles
   separate from USX styles.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Icon } from '../../components/Icon'
import { GlobalToolbar, ToolbarTab } from '../../components/GlobalToolbar'
import { useSurfaceShell } from '../../components/SurfaceShellContext'
import VaultSidebar from '../../components/VaultSidebar'
import StoryView from '../../components/StoryView'
import { FeedPanel } from '../gridui/panels/FeedPanel'
import { SettingsPanel } from './SettingsPanel'
import { GridUIContext } from '../gridui/GridUIStore'
import '../../styles/hub/index.css'
import '../../styles/global-toolbar.css'

// ─── Types ──────────────────────────────────────────────────────────
type SystemTab = 'install' | 'modules' | 'feeds' | 'story' | 'pages' | 'settings'

const SYSTEM_TABS: { id: SystemTab; icon: string; label: string }[] = [
  { id: 'install', icon: 'download', label: 'Install' },
  { id: 'modules', icon: 'apps', label: 'Modules' },
  { id: 'feeds', icon: 'rss_feed', label: 'Feeds' },
  { id: 'story', icon: 'auto_stories', label: 'Story Builder' },
  { id: 'pages', icon: 'menu_book', label: 'Pages' },
]

const SNACKBAR_API = 'http://localhost:8484'

// ─── S-Page Registry ────────────────────────────────────────────────
interface SPageDef {
  code: string
  title: string
  icon: string
  color: string
  description: string
  category: string
}

const S_PAGES: SPageDef[] = [
  // Core tools
  { code: 's100', title: 'Tool Builder', icon: 'build', color: '#58a6ff', description: 'Create and manage system tools.', category: 'Core' },
  { code: 's101', title: 'Story Builder', icon: 'auto_stories', color: '#58a6ff', description: 'Create and manage interactive stories.', category: 'Core' },
  { code: 's300', title: 'Workflow Builder', icon: 'account_tree', color: '#58a6ff', description: 'Design and manage automated workflows.', category: 'Core' },
  { code: 's600', title: 'Learning Hub', icon: 'school', color: '#a855f7', description: 'Tutorials, guides, and educational resources.', category: 'Core' },
  { code: 's800', title: 'Labs', icon: 'science', color: '#d29922', description: 'Experimental features and prototypes.', category: 'Core' },
  // System pages
  { code: 's110', title: 'System Boot', icon: 'power', color: '#00ff9d', description: 'System boot sequence and startup services.', category: 'System' },
  { code: 's120', title: 'System Config', icon: 'tune', color: '#f0883e', description: 'System configuration and environment settings.', category: 'System' },
  { code: 's130', title: 'System Status', icon: 'monitor_heart', color: '#3fb950', description: 'System health and status overview.', category: 'System' },
  { code: 's140', title: 'System Logs', icon: 'history', color: '#8b949e', description: 'System log viewer and diagnostics.', category: 'System' },
  { code: 's150', title: 'System Network', icon: 'network_check', color: '#58a6ff', description: 'Network configuration and connectivity.', category: 'System' },
  { code: 's160', title: 'System Security', icon: 'lock', color: '#f85149', description: 'Security settings and access control.', category: 'System' },
  { code: 's170', title: 'System Storage', icon: 'storage', color: '#d29922', description: 'Storage management and disk usage.', category: 'System' },
  { code: 's180', title: 'System Updates', icon: 'system_update', color: '#58a6ff', description: 'System update management.', category: 'System' },
  { code: 's200', title: 'Health Dashboard', icon: 'monitor_heart', color: '#3fb950', description: 'System health monitoring dashboard.', category: 'System' },
  { code: 's400', title: 'Maintenance', icon: 'build', color: '#f0883e', description: 'System maintenance and repair tools.', category: 'System' },
  { code: 's500', title: 'Log Viewer', icon: 'history', color: '#8b949e', description: 'System log viewer and analysis.', category: 'System' },
  { code: 's700', title: 'Security', icon: 'lock', color: '#f85149', description: 'Security settings and audit logs.', category: 'System' },
  { code: 's899', title: 'System Console', icon: 'terminal', color: '#00ff9d', description: 'System management console overlay.', category: 'System' },
]

// ─── Modules Panel ──────────────────────────────────────────────────
function ModulesPanel() {
  const modules = [
    { id: 'terminal', name: 'Terminal', subtitle: 'System Terminal', icon: 'terminal', color: '#58a6ff', desc: 'Full system terminal with SSH, tmux, and command history.' },
    { id: 'vault', name: 'Vault', subtitle: 'Document Store', icon: 'folder', color: '#22c55e', desc: 'Browse, search, and manage documents across all binders.' },
    { id: 'maps', name: 'Maps', subtitle: 'Spatial Grid', icon: 'map', color: '#f0883e', desc: 'Visual spatial grid system for surface layout management.' },
    { id: 'settings', name: 'Settings', subtitle: 'System Config', icon: 'tune', color: '#f59e0b', desc: 'Configure system preferences, themes, and surface settings.' },
    { id: 'usystem', name: 'uSystem', subtitle: 'System Pages Hub', icon: 'settings_suggest', color: '#58a6ff', desc: 'System information, health dashboard, diagnostics, maintenance, logs, network, security, storage, and console pages.', route: '/s100' },
    { id: 'vibe-agent', name: 'Vibe Agent', subtitle: 'Chat UI · OK Assistant', icon: 'school', color: '#a855f7', desc: 'AI-powered chat interface with Vibe Agent and Developer modes. Ask questions, run commands, and manage your workspace.', route: '/assistui' },
    { id: 'assistui', name: 'Assist', subtitle: 'Full-Page AI Chat', icon: 'smart_toy', color: '#a855f7', desc: 'Full-page AI chat with streaming responses, model selection, conversation management, and multi-agent support.', route: '/assistui' },
    { id: 'story-builder', name: 'Story Builder', subtitle: 'Step-by-step guides', icon: 'menu_book', color: '#22c55e', desc: 'Create step-by-step guides and walkthroughs for your workspace.', route: '/s101' },
    { id: 'workflow-builder', name: 'Workflow Builder', subtitle: 'Automated workflows', icon: 'account_tree', color: '#58a6ff', desc: 'Create and manage automated workflows with triggers for time, GitHub, vault, and more.', route: '/s300' },
    { id: 'tool-builder', name: 'Tool Builder', subtitle: 'Custom tool registry', icon: 'puzzle', color: '#f0883e', desc: 'Build and register custom tools for your workspace.', route: '/s100' },
  ]

  const openModule = (mod: any) => {
    if (mod.route) {
      window.location.href = mod.route
    }
  }

  return (
    <div className="hub-apps">
      <div className="hub-apps-section">
        <div className="hub-apps-section-header">
          <Icon name="apps" size={18} />
          <h3>Installed Modules</h3>
          <p>Tools and utilities available across surfaces</p>
        </div>

        <div className="hub-apps-grid">
          {modules.map(mod => (
            <div key={mod.id} className="hub-app-card" style={{ '--hub-app-color': mod.color } as React.CSSProperties}>
              <div className="hub-app-card-header">
                <div className="hub-app-card-icon" style={{ background: `${mod.color}20`, color: mod.color }}>
                  <Icon name={mod.icon} size={24} />
                </div>
                <div className="hub-app-card-info">
                  <h3 className="hub-app-card-title">{mod.name}</h3>
                  <p className="hub-app-card-subtitle" style={{ color: mod.color }}>{mod.subtitle}</p>
                </div>
              </div>
              <p className="hub-app-card-desc">{mod.desc}</p>
              <div className="hub-app-card-footer">
                <span className="hub-app-card-badge">System</span>
                <button className="hub-btn hub-btn--primary" onClick={() => openModule(mod)}>Open</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Install Panel ──────────────────────────────────────────────────
function InstallPanel() {
  const [activeSection, setActiveSection] = useState<'apps' | 'browser'>('apps')
  const [appStatuses, setAppStatuses] = useState<Record<string, 'checking' | 'installed' | 'running' | 'missing'>>({})
  const [ollamaModels, setOllamaModels] = useState<string[]>([])
  const [dockerContainers, setDockerContainers] = useState<number>(0)

  useEffect(() => {
    let cancelled = false

    async function probeAll() {
      const status: Record<string, 'checking' | 'installed' | 'running' | 'missing'> = {}

      // Ollama — probe port 11434
      try {
        const res = await fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(2000) })
        if (res.ok) {
          const data = await res.json()
          status.ollama = 'running'
          if (!cancelled) setOllamaModels((data.models || []).map((m: any) => m.name))
        } else {
          status.ollama = 'installed'
        }
      } catch {
        status.ollama = 'missing'
      }

      // Docker — probe socket via snackbar
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/docker/ps`, { signal: AbortSignal.timeout(2000) })
        if (res.ok) {
          const data = await res.json()
          status.docker = 'running'
          if (!cancelled) setDockerContainers(data.containers?.length || 0)
        } else {
          status.docker = 'installed'
        }
      } catch {
        try {
          const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'which docker' }),
            signal: AbortSignal.timeout(2000),
          })
          if (res.ok) {
            const data = await res.json()
            status.docker = data.stdout ? 'installed' : 'missing'
          } else {
            status.docker = 'missing'
          }
        } catch {
          status.docker = 'missing'
        }
      }

      // Node.js
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'node --version' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.nodejs = data.stdout ? 'installed' : 'missing'
        } else {
          status.nodejs = 'missing'
        }
      } catch {
        status.nodejs = 'missing'
      }

      // Git
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'git --version' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.git = data.stdout ? 'installed' : 'missing'
        } else {
          status.git = 'missing'
        }
      } catch {
        status.git = 'missing'
      }

      // Python
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'python3 --version' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.python = data.stdout ? 'installed' : 'missing'
        } else {
          status.python = 'missing'
        }
      } catch {
        status.python = 'missing'
      }

      // Go
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'go version' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.go = data.stdout ? 'installed' : 'missing'
        } else {
          status.go = 'missing'
        }
      } catch {
        status.go = 'missing'
      }

      // Rust/Cargo
      try {
        const res = await fetch(`${SNACKBAR_API}/v1/exec`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'cargo --version' }),
          signal: AbortSignal.timeout(2000),
        })
        if (res.ok) {
          const data = await res.json()
          status.rust = data.stdout ? 'installed' : 'missing'
        } else {
          status.rust = 'missing'
        }
      } catch {
        status.rust = 'missing'
      }

      if (!cancelled) setAppStatuses(status)
    }

    probeAll()
    return () => { cancelled = true }
  }, [])

  const statusIcon = (s: string) => {
    switch (s) {
      case 'running': return 'check_circle'
      case 'installed': return 'check_circle'
      case 'missing': return 'error'
      case 'checking': return 'sync'
      default: return 'help'
    }
  }

  const statusColor = (s: string) => {
    switch (s) {
      case 'running': return '#22c55e'
      case 'installed': return '#58a6ff'
      case 'missing': return '#f85149'
      case 'checking': return '#d29922'
      default: return '#8b949e'
    }
  }

  const apps = [
    { id: 'ollama', name: 'Ollama', icon: 'psychology', desc: 'Local LLM runtime', extra: ollamaModels.length > 0 ? `${ollamaModels.length} models` : undefined },
    { id: 'docker', name: 'Docker', icon: 'docker', desc: 'Container runtime', extra: dockerContainers > 0 ? `${dockerContainers} containers` : undefined },
    { id: 'nodejs', name: 'Node.js', icon: 'javascript', desc: 'JavaScript runtime' },
    { id: 'git', name: 'Git', icon: 'code', desc: 'Version control' },
    { id: 'python', name: 'Python', icon: 'code', desc: 'Python runtime' },
    { id: 'go', name: 'Go', icon: 'code', desc: 'Go runtime' },
    { id: 'rust', name: 'Rust/Cargo', icon: 'code', desc: 'Rust toolchain' },
  ]

  return (
    <div className="hub-apps">
      {/* ─── Section Toggle ─────────────────────────────────────── */}
      <div className="hub-apps-section-toggle">
        <button
          className={`hub-btn ${activeSection === 'apps' ? 'hub-btn--primary' : 'hub-btn--info'}`}
          onClick={() => setActiveSection('apps')}
        >
          <Icon name="apps" size={14} /> App Probes
        </button>
        <button
          className={`hub-btn ${activeSection === 'browser' ? 'hub-btn--primary' : 'hub-btn--info'}`}
          onClick={() => setActiveSection('browser')}
        >
          <Icon name="language" size={14} /> Zen Browser Mods
        </button>
      </div>

      {activeSection === 'apps' && (
        <div className="hub-apps-section">
          <div className="hub-apps-section-header">
            <Icon name="download" size={18} />
            <h3>App Probes</h3>
            <p>Detected tools and runtimes on this system</p>
          </div>

          <div className="hub-apps-grid">
            {apps.map(app => {
              const status = appStatuses[app.id] || 'checking'
              return (
                <div key={app.id} className="hub-app-card">
                  <div className="hub-app-card-header">
                    <div className="hub-app-card-icon" style={{ background: `${statusColor(status)}20`, color: statusColor(status) }}>
                      <Icon name={statusIcon(status)} size={24} />
                    </div>
                    <div className="hub-app-card-info">
                      <h3 className="hub-app-card-title">{app.name}</h3>
                      <p className="hub-app-card-subtitle" style={{ color: statusColor(status) }}>{status}</p>
                    </div>
                  </div>
                  <p className="hub-app-card-desc">{app.desc}</p>
                  {app.extra && (
                    <div className="hub-app-card-footer">
                      <span className="hub-app-card-badge">{app.extra}</span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {activeSection === 'browser' && (
        <div className="hub-apps-section">
          <div className="hub-apps-section-header">
            <Icon name="language" size={18} />
            <h3>Zen Browser Mods Setup</h3>
            <p>Configure Zen Browser with uConnect mods</p>
          </div>

          <div className="hub-apps-grid">
            <div className="hub-app-card">
              <div className="hub-app-card-header">
                <div className="hub-app-card-icon" style={{ background: '#58a6ff20', color: '#58a6ff' }}>
                  <Icon name="extension" size={24} />
                </div>
                <div className="hub-app-card-info">
                  <h3 className="hub-app-card-title">uConnect Mod</h3>
                  <p className="hub-app-card-subtitle" style={{ color: '#58a6ff' }}>Browser Extension</p>
                </div>
              </div>
              <p className="hub-app-card-desc">
                The uConnect mod adds sidebar integration, workspace templates, and quick-access tools to Zen Browser.
                Install from the <code>uconnect-mod/</code> directory in the uConnect workspace.
              </p>
              <div className="hub-app-card-footer">
                <span className="hub-app-card-badge">Manual Install</span>
                <button className="hub-btn hub-btn--primary" onClick={() => window.open('about:debugging#/runtime/this-firefox', '_blank')}>
                  Open Add-ons
                </button>
              </div>
            </div>

            <div className="hub-app-card">
              <div className="hub-app-card-header">
                <div className="hub-app-card-icon" style={{ background: '#d2992220', color: '#d29922' }}>
                  <Icon name="palette" size={24} />
                </div>
                <div className="hub-app-card-info">
                  <h3 className="hub-app-card-title">Zen Config</h3>
                  <p className="hub-app-card-subtitle" style={{ color: '#d29922' }}>userChrome / userContent</p>
                </div>
              </div>
              <p className="hub-app-card-desc">
                Custom CSS and JS for Zen Browser. Located in the <code>zen-config/</code> directory.
                Copy to your Firefox profile's <code>chrome/</code> directory.
              </p>
              <div className="hub-app-card-footer">
                <span className="hub-app-card-badge">Manual Setup</span>
                <button className="hub-btn hub-btn--primary" onClick={() => window.open('about:profiles', '_blank')}>
                  Open Profiles
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Pages Panel ────────────────────────────────────────────────────
function PagesPanel() {
  const [activeCategory, setActiveCategory] = useState<string>('All')
  const categories = ['All', ...new Set(S_PAGES.map(p => p.category))]

  const filtered = activeCategory === 'All'
    ? S_PAGES
    : S_PAGES.filter(p => p.category === activeCategory)

  return (
    <div className="hub-apps">
      <div className="hub-apps-section">
        <div className="hub-apps-section-header">
          <Icon name="menu_book" size={18} />
          <h3>System Pages</h3>
          <p>S100–S899 system page registry</p>
        </div>

        <div className="hub-apps-section-toggle">
          {categories.map(cat => (
            <button
              key={cat}
              className={`hub-btn ${activeCategory === cat ? 'hub-btn--primary' : 'hub-btn--info'}`}
              onClick={() => setActiveCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="hub-apps-grid">
          {filtered.map(page => (
            <div key={page.code} className="hub-app-card" style={{ '--hub-app-color': page.color } as React.CSSProperties}>
              <div className="hub-app-card-header">
                <div className="hub-app-card-icon" style={{ background: `${page.color}20`, color: page.color }}>
                  <Icon name={page.icon} size={24} />
                </div>
                <div className="hub-app-card-info">
                  <h3 className="hub-app-card-title">{page.title}</h3>
                  <p className="hub-app-card-subtitle" style={{ color: page.color }}>{page.code.toUpperCase()}</p>
                </div>
              </div>
              <p className="hub-app-card-desc">{page.description}</p>
              <div className="hub-app-card-footer">
                <span className="hub-app-card-badge">{page.category}</span>
                <button className="hub-btn hub-btn--primary" onClick={() => window.location.href = `/${page.code}`}>
                  Open
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Fallback GridUIContext for FeedPanel when rendered outside GridUI ──
function FeedPanelWithContext() {
  const fallbackStore = React.useMemo(() => ({
    showSnackbar: (msg: any) => console.log('[FeedPanel]', msg),
    activePanel: 'feeds' as const,
    setActivePanel: () => {},
    activePanelMeta: null,
    isDark: true,
    toggleTheme: () => {},
    fontSize: 14,
    increaseFontSize: () => {},
    decreaseFontSize: () => {},
    setFontSize: () => {},
    fontStyle: 'sans' as const,
    setFontStyle: () => {},
    gridFont: 'petme128' as const,
    setGridFont: () => {},
    viewport: { cols: 48, rows: 36, zoom: 1, bgColor: '#0d1117', gridColor: '#21262d', textColor: '#e6edf3', surfaceBgColor: '#010409', borderMode: 1 as const, borderBgColor: '#0d1117' },
    setViewport: () => {},
    applyViewportPreset: () => {},
    viewportPopupOpen: false,
    toggleViewportPopup: () => {},
    terminalViewport: { cols: 64, rows: 36, zoom: 1, bgColor: '#0d1117', gridColor: '#21262d', textColor: '#e6edf3', surfaceBgColor: '#010409', borderMode: 1 as const, borderBgColor: '#0d1117' },
    teletextViewport: { cols: 48, rows: 36, zoom: 1, bgColor: '#0d1117', gridColor: '#21262d', textColor: '#e6edf3', surfaceBgColor: '#010409', borderMode: 1 as const, borderBgColor: '#0d1117' },
    gridLayers: [],
    toggleLayer: () => {},
    setLayerVisibility: () => {},
    setLayerOpacity: () => {},
    addLayer: () => {},
    removeLayer: () => {},
    displayMode: 'teletext' as const,
    setGridDisplayMode: () => {},
    gridCells: [],
    setGridCells: () => {},
    updateCell: () => {},
    navRailCollapsed: false,
    toggleNavRail: () => {},
    activeSnackbar: null,
    dismissSnackbar: () => {},
  }), [])
  return (
    <GridUIContext.Provider value={fallbackStore as any}>
      <FeedPanel />
    </GridUIContext.Provider>
  )
}

// ─── Main Component ────────────────────────────────────────────────
export default function USystemSurface() {

  const location = useLocation()
  const navigate = useNavigate()
  const { sidebarOpen, toggleSidebar } = useSurfaceShell()

  // Derive active tab from URL query param on every location change.
  // This avoids flash: the tab is computed synchronously during render,
  // and updates immediately when the URL changes (e.g. gear icon → /system?tab=settings).
  const activeTab: SystemTab = (() => {
    const params = new URLSearchParams(location.search)
    const tabParam = params.get('tab')
    const validTabs: SystemTab[] = ['install', 'modules', 'feeds', 'story', 'pages', 'settings']
    if (tabParam && (validTabs as string[]).includes(tabParam)) {
      return tabParam as SystemTab
    }
    return 'install'
  })()

  const renderContent = () => {
    switch (activeTab) {
      case 'install':
        return <InstallPanel />
      case 'modules':
        return <ModulesPanel />
      case 'feeds':
        return <FeedPanelWithContext />
      case 'story':
        return <StoryView />
      case 'pages':
        return <PagesPanel />
      case 'settings':
        return <SettingsPanel />
      default:
        return <InstallPanel />
    }
  }

  return (
    <div className="usx-surface-layout">
      <GlobalToolbar
        tabs={SYSTEM_TABS.map(t => ({
          id: t.id,
          icon: t.icon,
          label: t.label,
          active: activeTab === t.id,
          onClick: () => navigate(`/system?tab=${t.id}`),
        }))}
        onToggleSidebar={toggleSidebar}
        sidebarOpen={sidebarOpen}
      />
      <div className="usx-surface-body">
        <VaultSidebar open={sidebarOpen} onToggle={toggleSidebar} />
        <main className="usx-surface-main">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}
