import React, { useEffect, useMemo, useState } from 'react'
import { Icon } from '../../components/Icon'
import VaultSidebar, { type SidebarNavItem } from '../../components/VaultSidebar'
import { GlobalToolbar, type ToolbarTab } from '../../components/GlobalToolbar'
import { GridUIContext, useGridUIStore } from '../gridui/GridUIStore'
import { TerminalPanel } from '../gridui/panels/TerminalPanel'
import { TeletextGrid } from '../gridui/panels/TeletextGrid'
import { GRID_TOOL_VIEWS } from './gridToolset'

type UCodeTopTab = 'terminal' | 'teletext'
type SidebarMode = 'server' | 'filepicker'
type DashboardToolTab = 'overview' | 'gridsmith' | 'grid-editor' | 'layer-composer' | 'svg-font-mapper' | 'map-rendering' | 'spatial-algebra'

const SNACKBAR_API = 'http://localhost:8484'

interface GridSmithMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function UCodeSurface() {
  const store = useGridUIStore()
  const [topTab, setTopTab] = useState<UCodeTopTab>('terminal')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarMode, setSidebarMode] = useState<SidebarMode>('server')
  const [toolTab, setToolTab] = useState<DashboardToolTab>('overview')
  const [gridsmithChatOpen, setGridSmithChatOpen] = useState(false)
  const [gridsmithPrompt, setGridSmithPrompt] = useState('')
  const [gridsmithLoading, setGridSmithLoading] = useState(false)
  const [gridsmithMessages, setGridSmithMessages] = useState<GridSmithMessage[]>([
    {
      role: 'assistant',
      content: 'GridSmith ready. Ask about world-building, import a BASIC program, or plan layers and maps for the live uCode workspace.',
    },
  ])
  const [basicProgram, setBasicProgram] = useState('10 PRINT "HELLO, WORLD"\n20 GOTO 10')
  const [importNotice, setImportNotice] = useState<string | null>(null)

  useEffect(() => {
    store.setActivePanel(topTab)
  }, [store, topTab])

  const toolbarTabs: ToolbarTab[] = useMemo(
    () => [
      {
        id: 'terminal',
        icon: 'terminal',
        label: 'Terminal',
        active: topTab === 'terminal',
        onClick: () => setTopTab('terminal'),
      },
      {
        id: 'teletext',
        icon: 'tv',
        label: 'Teletext',
        active: topTab === 'teletext',
        onClick: () => setTopTab('teletext'),
      },
    ],
    [topTab],
  )

  const serverNavItems: SidebarNavItem[] = [
    { id: 'overview', icon: 'dashboard', label: 'Dashboard', active: toolTab === 'overview', onClick: () => setToolTab('overview') },
    { id: 'gridsmith', icon: 'smart_toy', label: 'GridSmith', active: toolTab === 'gridsmith', onClick: () => setToolTab('gridsmith') },
    { id: 'grid-editor', icon: 'draw', label: 'Grid Editor', active: toolTab === 'grid-editor', onClick: () => setToolTab('grid-editor') },
    { id: 'layer-composer', icon: 'layers', label: 'Layer Composer', active: toolTab === 'layer-composer', onClick: () => setToolTab('layer-composer') },
    { id: 'svg-font-mapper', icon: 'font_download', label: 'SVG Font Mapper', active: toolTab === 'svg-font-mapper', onClick: () => setToolTab('svg-font-mapper') },
    { id: 'map-rendering', icon: 'map', label: 'Map Rendering', active: toolTab === 'map-rendering', onClick: () => setToolTab('map-rendering') },
    { id: 'spatial-algebra', icon: 'explore', label: 'Spatial Algebra', active: toolTab === 'spatial-algebra', onClick: () => setToolTab('spatial-algebra') },
  ]

  const activeTool = GRID_TOOL_VIEWS.find(view => view.id === toolTab)

  const sendGridSmithPrompt = async () => {
    const prompt = gridsmithPrompt.trim()
    if (!prompt || gridsmithLoading) return
    setGridSmithLoading(true)
    setGridSmithMessages(prev => [...prev, { role: 'user', content: prompt }])
    setGridSmithPrompt('')
    try {
      const res = await fetch(`${SNACKBAR_API}/api/agents/spec/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_type: 'worldbuild',
          complexity: 'medium',
          messages: [{ role: 'user', content: prompt }],
        }),
      })
      const data = await res.json()
      const reply = data?.response?.message || data?.response?.content || JSON.stringify(data, null, 2)
      setGridSmithMessages(prev => [...prev, { role: 'assistant', content: String(reply) }])
    } catch (error) {
      setGridSmithMessages(prev => [...prev, { role: 'assistant', content: `GridSmith agent error: ${String(error)}` }])
    } finally {
      setGridSmithLoading(false)
    }
  }

  const importBasicToGridSmith = async () => {
    setImportNotice(null)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/gridsmith/world/import-basic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          program: basicProgram,
          world_name: 'UCode BASIC Import',
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`)
      setImportNotice(`Imported BASIC world: ${data?.world?.id || 'ok'}`)
      setGridSmithMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Imported BASIC program into GridSmith workspace. Manifest: ${data?.files?.manifest || 'n/a'}` },
      ])
    } catch (error) {
      setImportNotice(`Import failed: ${String(error)}`)
    }
  }

  return (
    <GridUIContext.Provider value={store}>
      <div className="ucode-surface">
        <GlobalToolbar
          tabs={toolbarTabs}
          onToggleSidebar={() => setSidebarOpen(prev => !prev)}
          sidebarOpen={sidebarOpen}
          sidebarToggleLabel="uCode sidebar"
          hideGlobe
        />

        <div className="usx-surface-body ucode-body">
          <VaultSidebar
            open={sidebarOpen}
            showModeTabs
            sidebarMode={sidebarMode}
            onSidebarModeChange={setSidebarMode}
            serverNavItems={serverNavItems}
          />

          <main className="usx-surface-main ucode-main">
            <section className="ucode-main-viewport">
              <div className="ucode-main-viewport-header">
                <span className="ucode-pill">uCode Surface</span>
                <span className="ucode-pill ucode-pill--accent">{topTab === 'terminal' ? 'Terminal Mode' : 'Teletext Mode'}</span>
              </div>
              <div className="ucode-main-viewport-body">
                {topTab === 'terminal' ? <TerminalPanel /> : <TeletextGrid />}
              </div>
            </section>

            <aside className="ucode-dashboard">
              <div className="ucode-dashboard-header">
                <div>
                  <h2>Unified Grid Toolset</h2>
                  <p>Consolidated GridCore upgrade track and implementation status.</p>
                </div>
                <span className="ucode-pill">LOCKED BRIEF</span>
              </div>

              {toolTab === 'overview' ? (
                <div className="ucode-tool-grid">
                  {GRID_TOOL_VIEWS.map(view => (
                    <button key={view.id} className="ucode-tool-card" onClick={() => setToolTab(view.id as DashboardToolTab)}>
                      <div className="ucode-tool-card-title">{view.name}</div>
                      <div className="ucode-tool-card-subtitle">{view.subtitle}</div>
                      <div className="ucode-tool-card-summary">{view.summary}</div>
                    </button>
                  ))}
                </div>
              ) : toolTab === 'gridsmith' ? (
                <div className="ucode-tool-detail">
                  <h3>GridSmith Workspace</h3>
                  <p>Contained world-building agent for GridCore, wired to the live uCode workspace and uCore bridge.</p>

                  <div className="ucode-tool-detail-section">
                    <h4>Import BASIC</h4>
                    <textarea
                      value={basicProgram}
                      onChange={e => setBasicProgram(e.target.value)}
                      spellCheck={false}
                      style={{ width: '100%', minHeight: 140, borderRadius: 8, padding: 12, background: 'var(--pico-card-background-color, #11161c)', color: 'var(--pico-color, #c9d1d9)', border: '1px solid var(--pico-muted-border-color, #30363d)' }}
                    />
                    <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                      <button className="ucode-back-btn" onClick={importBasicToGridSmith}>
                        <Icon name="publish" size={14} />
                        Import into GridSmith
                      </button>
                      <button className="ucode-back-btn" onClick={() => setGridSmithChatOpen(true)}>
                        <Icon name="smart_toy" size={14} />
                        Open GridSmith Agent
                      </button>
                    </div>
                    {importNotice && <p style={{ marginTop: 8 }}>{importNotice}</p>}
                  </div>

                  <div className="ucode-tool-detail-section">
                    <h4>API Surface</h4>
                    <ul>
                      <li>POST /api/gridsmith/world/import-basic</li>
                      <li>GET /api/gridsmith/tools</li>
                      <li>POST /api/agents/spec/route task_type=worldbuild</li>
                    </ul>
                  </div>

                  <button className="ucode-back-btn" onClick={() => setToolTab('overview')}>
                    <Icon name="arrow_back" size={14} />
                    Back to Dashboard
                  </button>
                </div>
              ) : activeTool ? (
                <div className="ucode-tool-detail">
                  <h3>{activeTool.name}</h3>
                  <p>{activeTool.summary}</p>

                  <div className="ucode-tool-detail-section">
                    <h4>API Surface</h4>
                    <ul>
                      {activeTool.apis.map(api => (
                        <li key={api}>{api}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="ucode-tool-detail-section">
                    <h4>Upgrade Goals</h4>
                    <ul>
                      {activeTool.upgrade.map(item => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>

                  <button className="ucode-back-btn" onClick={() => setToolTab('overview')}>
                    <Icon name="arrow_back" size={14} />
                    Back to Dashboard
                  </button>
                </div>
              ) : null}
            </aside>
          </main>

          {gridsmithChatOpen && (
            <div style={{ position: 'fixed', right: 16, top: 72, width: 400, height: 'calc(100vh - 110px)', zIndex: 1000, background: 'var(--pico-card-background-color, #0d1117)', border: '1px solid var(--pico-muted-border-color, #30363d)', borderRadius: 16, overflow: 'hidden', boxShadow: '0 18px 50px rgba(0,0,0,0.35)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 14px', borderBottom: '1px solid var(--pico-muted-border-color, #30363d)' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontWeight: 700 }}>
                  <Icon name="smart_toy" size={16} />
                  GridSmith Dev Agent
                </span>
                <button className="usx-header-btn" onClick={() => setGridSmithChatOpen(false)} title="Close GridSmith chat">
                  <Icon name="close" size={16} />
                </button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100% - 52px)' }}>
                <div style={{ flex: 1, overflow: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {gridsmithMessages.map((message, index) => (
                    <div key={`${message.role}-${index}`} style={{ alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '92%', padding: '10px 12px', borderRadius: 12, background: message.role === 'user' ? 'rgba(88,166,255,0.18)' : 'rgba(255,255,255,0.04)', whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.45 }}>
                      {message.content}
                    </div>
                  ))}
                  {gridsmithLoading && <div style={{ fontSize: 12, color: 'var(--pico-muted-color, #8b949e)' }}>GridSmith is thinking…</div>}
                </div>
                <div style={{ padding: 12, borderTop: '1px solid var(--pico-muted-border-color, #30363d)' }}>
                  <textarea
                    value={gridsmithPrompt}
                    onChange={e => setGridSmithPrompt(e.target.value)}
                    placeholder="Ask GridSmith to plan layers, import worlds, or map coordinates…"
                    spellCheck={false}
                    style={{ width: '100%', minHeight: 88, borderRadius: 10, padding: 10, resize: 'vertical', background: 'var(--pico-background-color, #010409)', color: 'var(--pico-color, #c9d1d9)', border: '1px solid var(--pico-muted-border-color, #30363d)' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginTop: 8 }}>
                    <button className="ucode-back-btn" onClick={() => setGridSmithPrompt('Design a dungeon world with terrain, collision, and entities layers.')}>Prompt</button>
                    <button className="ucode-back-btn" onClick={sendGridSmithPrompt}>
                      <Icon name="send" size={14} />
                      Send
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={() => setGridSmithChatOpen(prev => !prev)}
            title={gridsmithChatOpen ? 'Close GridSmith agent' : 'Open GridSmith agent'}
            aria-label="Toggle GridSmith agent"
            style={{ position: 'fixed', right: 20, bottom: 18, zIndex: 1001, width: 62, height: 62, borderRadius: '50%', border: '1px solid rgba(88,166,255,0.35)', background: gridsmithChatOpen ? 'linear-gradient(135deg, #1f6feb, #58a6ff)' : 'linear-gradient(135deg, #11161c, #1c2430)', color: '#fff', boxShadow: '0 10px 28px rgba(0,0,0,0.35)', cursor: 'pointer' }}
          >
            <Icon name={gridsmithChatOpen ? 'close' : 'smart_toy'} size={24} />
          </button>
        </div>
      </div>
    </GridUIContext.Provider>
  )
}
