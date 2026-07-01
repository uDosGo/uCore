/* ═══════════════════════════════════════════════════════════════════
   MCPServersPanel — USX Schema v3.1 MCP Server Dashboard
   ═══════════════════════════════════════════════════════════════════
   Real-time dashboard for MCP (Model Context Protocol) servers.
   Shows status, health, tool counts, and recent activity.
   Project Type: Technical (TC) | Autonomy Level: L4 (Delegator)
   Binder: ⚙️ Technical/Developer | Tags: #mcp #model-context-protocol #dashboard
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'

interface MCPServer {
  id: string
  name: string
  version: string
  port: number
  status: 'online' | 'offline' | 'error'
  tools: string[]
  lastCheck?: string
}

const MCP_SERVERS: MCPServer[] = [
  { id: 'playwright', name: 'Playwright MCP', version: '0.0.76', port: 8931, status: 'online', tools: ['navigate', 'click', 'fill', 'screenshot', 'extract', 'evaluate', 'wait', 'close'] },
  { id: 'firewatch', name: 'Firewatch MCP', version: '1.5.0', port: 8932, status: 'offline', tools: ['navigate', 'click', 'fill', 'screenshot', 'extract', 'evaluate'] },
  { id: 'secrets', name: 'Secrets Broker', version: '1.0.4', port: 8933, status: 'offline', tools: ['get', 'set', 'list', 'delete', 'rotate'] },
  { id: 'scheduler', name: 'Feed Sage', version: '0.1.6', port: 8935, status: 'offline', tools: ['add', 'remove', 'list', 'run', 'status'] },
  { id: 'serena', name: 'Serena Slim', version: '0.0.1-slim.1.10', port: 8936, status: 'offline', tools: ['analyze', 'check_imports', 'check_symbols', 'check_api', 'suggest_fixes'] },
]

export function MCPServersPanel() {
  const [servers, setServers] = useState<MCPServer[]>(MCP_SERVERS)
  const [loading, setLoading] = useState(false)

  const checkServerHealth = async (server: MCPServer): Promise<MCPServer> => {
    try {
      const response = await fetch(`http://localhost:${server.port}/health`, {
        signal: AbortSignal.timeout(3000),
      })
      if (response.ok) {
        return { ...server, status: 'online', lastCheck: new Date().toISOString() }
      }
    } catch {
      return { ...server, status: 'offline', lastCheck: new Date().toISOString() }
    }
    return server
  }

  const refreshServers = async () => {
    setLoading(true)
    const updated = await Promise.all(servers.map(checkServerHealth))
    setServers(updated)
    setLoading(false)
  }

  useEffect(() => {
    refreshServers()
    const interval = setInterval(refreshServers, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return '#3fb950'
      case 'offline': return '#f85149'
      case 'error': return '#d29922'
      default: return '#8b949e'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return 'check_circle'
      case 'offline': return 'cancel'
      case 'error': return 'error'
      default: return 'help'
    }
  }

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">MCP Server Dashboard</h3>
        <button
          className="developer-repo-btn"
          onClick={refreshServers}
          disabled={loading}
          title={loading ? 'Refreshing...' : 'Refresh servers'}
        >
          <Icon name={loading ? 'refresh' : 'refresh'} size={14} />
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="developer-settings-section">
        <h4 className="developer-settings-section-title">
          <Icon name="dns" size={16} /> MCP Servers
        </h4>
        <div className="hub-settings-fontsize-controls" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: 'var(--usx-spacing-lg)' }}>
          {servers.map(server => (
            <div key={server.id} className={`hub-settings-fontsize-btn hub-settings-fontsize-btn--${server.status}`} style={{
              padding: 'var(--usx-spacing-lg)',
              borderRadius: 'var(--usx-radius-lg)',
              border: `1px solid ${server.status === 'online' ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)'}`,
              background: 'var(--pico-card-background-color, #161b22)',
              color: 'var(--pico-color, #c9d1d9)',
              cursor: 'default',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--usx-spacing-md)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 'var(--usx-spacing-md)', borderBottom: '1px solid var(--pico-border-color, #30363d)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--usx-spacing-md)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', background: 'var(--pico-card-sectioning-background-color, #1c2128)', borderRadius: 'var(--usx-radius-md)', color: 'var(--pico-color, #c9d1d9)' }}>
                    <Icon name="dns" size={20} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h4 style={{ margin: 0, fontSize: 'var(--usx-font-size-h4)', fontWeight: 'var(--usx-font-weight-heading)', color: 'var(--pico-color, #c9d1d9)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{server.name}</h4>
                    <span style={{ fontSize: 'var(--usx-font-size-meta)', color: 'var(--pico-muted-color, #8b949e)' }}>v{server.version}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--usx-spacing-xs)', fontSize: 'var(--usx-font-size-meta)', color: 'var(--pico-muted-color, #8b949e)' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: getStatusColor(server.status), animation: 'pulse 2s ease-in-out infinite' }} />
                    <span>{server.status}</span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--usx-spacing-sm)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 'var(--usx-font-size-body)' }}>
                  <span style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Port</span>
                  <span style={{ color: 'var(--pico-color, #c9d1d9)', fontWeight: 500 }}>{server.port}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 'var(--usx-font-size-body)' }}>
                  <span style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Tools</span>
                  <span style={{ color: 'var(--pico-color, #c9d1d9)', fontWeight: 500 }}>{server.tools.length}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 'var(--usx-font-size-body)' }}>
                  <span style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Last Check</span>
                  <span style={{ color: 'var(--pico-color, #c9d1d9)', fontWeight: 500 }}>
                    {server.lastCheck ? new Date(server.lastCheck).toLocaleTimeString() : 'Never'}
                  </span>
                </div>
              </div>

              <div style={{ paddingTop: 'var(--usx-spacing-md)', borderTop: '1px solid var(--pico-border-color, #30363d)' }}>
                <span style={{ fontSize: 'var(--usx-font-size-meta)', color: 'var(--pico-muted-color, #8b949e)' }}>Available Tools:</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--usx-spacing-xs)', marginTop: 'var(--usx-spacing-xs)' }}>
                  {server.tools.map(tool => (
                    <span key={tool} style={{
                      padding: 'var(--usx-spacing-xs) var(--usx-spacing-sm)',
                      background: 'var(--pico-card-sectioning-background-color, #1c2128)',
                      border: '1px solid var(--pico-border-color, #30363d)',
                      borderRadius: 'var(--usx-radius-sm)',
                      fontSize: 'var(--usx-font-size-meta)',
                      color: 'var(--pico-color, #c9d1d9)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '200px',
                    }}>
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="developer-settings-section">
        <h4 className="developer-settings-section-title">
          <Icon name="analytics" size={16} /> Statistics
        </h4>
        <div style={{ display: 'flex', gap: 'var(--usx-spacing-xl)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--usx-spacing-xs)' }}>
            <span style={{ fontSize: 'var(--usx-font-size-h2)', fontWeight: 'var(--usx-font-weight-heading)', color: 'var(--pico-color, #c9d1d9)' }}>{servers.filter(s => s.status === 'online').length}</span>
            <span style={{ fontSize: 'var(--usx-font-size-meta)', color: 'var(--pico-muted-color, #8b949e)' }}>Online</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--usx-spacing-xs)' }}>
            <span style={{ fontSize: 'var(--usx-font-size-h2)', fontWeight: 'var(--usx-font-weight-heading)', color: 'var(--pico-color, #c9d1d9)' }}>{servers.filter(s => s.status === 'offline').length}</span>
            <span style={{ fontSize: 'var(--usx-font-size-meta)', color: 'var(--pico-muted-color, #8b949e)' }}>Offline</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--usx-spacing-xs)' }}>
            <span style={{ fontSize: 'var(--usx-font-size-h2)', fontWeight: 'var(--usx-font-weight-heading)', color: 'var(--pico-color, #c9d1d9)' }}>{servers.length}</span>
            <span style={{ fontSize: 'var(--usx-font-size-meta)', color: 'var(--pico-muted-color, #8b949e)' }}>Total</span>
          </div>
        </div>
      </div>
    </div>
  )
}