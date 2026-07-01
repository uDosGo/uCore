/* ═══════════════════════════════════════════════════════════════════
   GridCoreDashboard — Status overview for uCode surface
   ═══════════════════════════════════════════════════════════════════
   Shows key stats, system status, MCP server status, and feed status.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useEffect, useState } from 'react'
import { Icon } from '../../components/Icon'

interface StatusItem {
  id: string
  name: string
  status: 'running' | 'stopped' | 'error' | 'unknown'
  port?: number
  uptime?: string
  message?: string
}

interface FeedStatus {
  id: string
  name: string
  type: 'rss' | 'atom' | 'json'
  status: 'active' | 'paused' | 'error'
  lastUpdate?: string
  itemCount?: number
}

interface MCPStatus {
  id: string
  name: string
  status: 'connected' | 'disconnected' | 'error'
  tools?: number
  resources?: number
}

const SNACKBAR_API = 'http://localhost:8484'

export function GridCoreDashboard() {
  const [systemStatus, setSystemStatus] = useState<StatusItem[]>([
    { id: 'snackbar', name: 'Snackbar API', status: 'unknown', port: 8484 },
    { id: 'bbcsdl', name: 'BBCSDL Bridge', status: 'unknown', port: 8485 },
    { id: 'ceefax', name: 'Ceefax Server', status: 'unknown', port: 8486 },
  ])
  
  const [mcpStatus, setMcpStatus] = useState<MCPStatus[]>([
    { id: 'filesystem', name: 'Filesystem MCP', status: 'disconnected' },
    { id: 'memory', name: 'Memory MCP', status: 'disconnected' },
    { id: 'github', name: 'GitHub MCP', status: 'disconnected' },
    { id: 'brave-search', name: 'Brave Search MCP', status: 'disconnected' },
  ])
  
  const [feedStatus, setFeedStatus] = useState<FeedStatus[]>([
    { id: 'bbc-news', name: 'BBC News', type: 'rss', status: 'active', lastUpdate: '2m ago', itemCount: 25 },
    { id: 'hacker-news', name: 'Hacker News', type: 'rss', status: 'active', lastUpdate: '5m ago', itemCount: 30 },
    { id: 'reddit-tech', name: 'Reddit Tech', type: 'rss', status: 'paused', lastUpdate: '1h ago', itemCount: 15 },
  ])
  
  const [stats, setStats] = useState({
    terminalSessions: 3,
    teletextPages: 42,
    gridLayers: 6,
    activeFeeds: 2,
    mcpConnected: 0,
    uptime: '2h 34m',
  })

  // Fetch real status from Snackbar API
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const resp = await fetch(`${SNACKBAR_API}/api/status`)
        if (resp.ok) {
          const data = await resp.json()
          // Update status based on response
          if (data.services) {
            setSystemStatus(prev => prev.map(s => ({
              ...s,
              status: data.services[s.id]?.status || 'unknown',
              uptime: data.services[s.id]?.uptime,
            })))
          }
          if (data.mcp) {
            setMcpStatus(prev => prev.map(m => ({
              ...m,
              status: data.mcp[m.id]?.status || 'disconnected',
              tools: data.mcp[m.id]?.tools,
              resources: data.mcp[m.id]?.resources,
            })))
          }
          if (data.feeds) {
            setFeedStatus(prev => prev.map(f => ({
              ...f,
              status: data.feeds[f.id]?.status || 'active',
              lastUpdate: data.feeds[f.id]?.lastUpdate,
              itemCount: data.feeds[f.id]?.itemCount,
            })))
          }
          if (data.stats) {
            setStats(prev => ({ ...prev, ...data.stats }))
          }
        }
      } catch {
        // Snackbar not available, show default status
      }
    }
    
    fetchStatus()
    const interval = setInterval(fetchStatus, 30000) // Poll every 30s
    return () => clearInterval(interval)
  }, [])

  const statusColor = (status: string) => {
    switch (status) {
      case 'running':
      case 'connected':
      case 'active':
        return '#238636'
      case 'stopped':
      case 'disconnected':
      case 'paused':
        return '#8b949e'
      case 'error':
        return '#da3633'
      default:
        return '#6e7681'
    }
  }

  return (
    <div className="gridcore-dashboard">
      {/* Header */}
      <div className="gridcore-dashboard-header">
        <h2>GridCore Dashboard</h2>
        <p>System status and overview</p>
      </div>

      {/* Statistics */}
      <section className="gridcore-section">
        <h3>
          <Icon name="bar_chart" size={16} />
          Statistics
        </h3>
        <div className="gridcore-stats-grid">
          <div className="gridcore-stat-card">
            <div className="gridcore-stat-value">{stats.terminalSessions}</div>
            <div className="gridcore-stat-label">Terminal Sessions</div>
          </div>
          <div className="gridcore-stat-card">
            <div className="gridcore-stat-value">{stats.teletextPages}</div>
            <div className="gridcore-stat-label">Teletext Pages</div>
          </div>
          <div className="gridcore-stat-card">
            <div className="gridcore-stat-value">{stats.gridLayers}</div>
            <div className="gridcore-stat-label">Grid Layers</div>
          </div>
          <div className="gridcore-stat-card">
            <div className="gridcore-stat-value">{stats.activeFeeds}</div>
            <div className="gridcore-stat-label">Active Feeds</div>
          </div>
          <div className="gridcore-stat-card">
            <div className="gridcore-stat-value">{stats.mcpConnected}</div>
            <div className="gridcore-stat-label">MCP Connected</div>
          </div>
          <div className="gridcore-stat-card">
            <div className="gridcore-stat-value">{stats.uptime}</div>
            <div className="gridcore-stat-label">Uptime</div>
          </div>
        </div>
      </section>

      {/* System Status */}
      <section className="gridcore-section">
        <h3>
          <Icon name="dns" size={16} />
          System Status
        </h3>
        <div className="gridcore-status-list">
          {systemStatus.map(item => (
            <div key={item.id} className="gridcore-status-item">
              <div className="gridcore-status-indicator" style={{ backgroundColor: statusColor(item.status) }} />
              <div className="gridcore-status-info">
                <span className="gridcore-status-name">{item.name}</span>
                {item.port && <span className="gridcore-status-port">:{item.port}</span>}
              </div>
              <div className="gridcore-status-meta">
                <span className="gridcore-status-badge" style={{ color: statusColor(item.status) }}>
                  {item.status}
                </span>
                {item.uptime && <span className="gridcore-status-uptime">{item.uptime}</span>}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* MCP Status */}
      <section className="gridcore-section">
        <h3>
          <Icon name="hub" size={16} />
          MCP Servers
        </h3>
        <div className="gridcore-status-list">
          {mcpStatus.map(item => (
            <div key={item.id} className="gridcore-status-item">
              <div className="gridcore-status-indicator" style={{ backgroundColor: statusColor(item.status) }} />
              <div className="gridcore-status-info">
                <span className="gridcore-status-name">{item.name}</span>
              </div>
              <div className="gridcore-status-meta">
                {item.tools !== undefined && (
                  <span className="gridcore-status-count">{item.tools} tools</span>
                )}
                <span className="gridcore-status-badge" style={{ color: statusColor(item.status) }}>
                  {item.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Feed Status */}
      <section className="gridcore-section">
        <h3>
          <Icon name="rss_feed" size={16} />
          Feed Status
        </h3>
        <div className="gridcore-status-list">
          {feedStatus.map(item => (
            <div key={item.id} className="gridcore-status-item">
              <div className="gridcore-status-indicator" style={{ backgroundColor: statusColor(item.status) }} />
              <div className="gridcore-status-info">
                <span className="gridcore-status-name">{item.name}</span>
                <span className="gridcore-status-type">{item.type.toUpperCase()}</span>
              </div>
              <div className="gridcore-status-meta">
                {item.itemCount !== undefined && (
                  <span className="gridcore-status-count">{item.itemCount} items</span>
                )}
                {item.lastUpdate && (
                  <span className="gridcore-status-time">{item.lastUpdate}</span>
                )}
                <span className="gridcore-status-badge" style={{ color: statusColor(item.status) }}>
                  {item.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Actions */}
      <section className="gridcore-section">
        <h3>
          <Icon name="bolt" size={16} />
          Quick Actions
        </h3>
        <div className="gridcore-actions">
          <button className="gridcore-action-btn">
            <Icon name="refresh" size={14} />
            Refresh All
          </button>
          <button className="gridcore-action-btn">
            <Icon name="play_arrow" size={14} />
            Start All Services
          </button>
          <button className="gridcore-action-btn">
            <Icon name="stop" size={14} />
            Stop All Services
          </button>
          <button className="gridcore-action-btn">
            <Icon name="settings" size={14} />
            Configure
          </button>
        </div>
      </section>
    </div>
  )
}
