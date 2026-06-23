/* ═══════════════════════════════════════════════════════════════════
   AgentsPanel — Special Agent Configuration Dashboard (USX)
   ═══════════════════════════════════════════════════════════════════
   USX-styled agent cards with priority, model, provider, capabilities,
   expandable details, and task routing info.
   Consumed by: DeveloperSurface, UServerSurface
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'

const SNACKBAR_API = 'http://localhost:8484'

interface Agent {
  id: string
  name: string
  description: string
  model: string
  provider: string
  capabilities: string[]
  cost_per_task: number
  timeout: number
  priority: number
}

export function AgentsPanel() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)

  const loadAgents = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${SNACKBAR_API}/api/agents/spec/list`, {
        signal: AbortSignal.timeout(4000),
      })
      if (res.ok) {
        const data = await res.json()
        setAgents(data.agents || [])
      }
    } catch (e) {
      console.error('Failed to load agents:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadAgents()
  }, [])

  const providerColor = (provider: string) => {
    switch (provider?.toLowerCase()) {
      case 'ollama':    return '#58a6ff'
      case 'openrouter': return '#3fb950'
      case 'openai':    return '#79c0ff'
      default:          return '#8b949e'
    }
  }

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '0 16px 16px' }}>
      {/* Header */}
      <div className="userver-toolbar" style={{ padding: '12px 0' }}>
        <div className="userver-toolbar-left">
          <h2 className="userver-heading" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name="smart_toy" size={20} />
            Special Agents
          </h2>
          <span className="userver-card-subtitle">
            {loading ? 'Loading\u2026' : `${agents.length} agents \u00b7 priority-sorted`}
          </span>
        </div>
        <div className="userver-toolbar-actions" style={{ marginLeft: 'auto' }}>
          <button className="userver-action-btn" onClick={() => void loadAgents()} disabled={loading}>
            {loading ? 'Refreshing\u2026' : 'Refresh'}
          </button>
        </div>
      </div>

      {!loading && agents.length === 0 && (
        <div className="userver-card" style={{ marginTop: 8, textAlign: 'center', padding: 24 }}>
          <p className="userver-text" style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
            No agents configured. Use <code>/api/agents/spec/list</code> to register agents.
          </p>
        </div>
      )}

      {/* Agent Cards — USX-styled */}
      <div className="userver-grid">
        {agents.sort((a, b) => a.priority - b.priority).map(agent => {
          const isSelected = selectedAgent === agent.id
          return (
            <div
              key={agent.id}
              className="userver-card"
              style={{
                borderLeft: `3px solid ${providerColor(agent.provider)}`,
                cursor: 'pointer',
                transition: 'all 120ms',
                borderColor: isSelected ? providerColor(agent.provider) : undefined,
                boxShadow: isSelected ? `0 0 8px ${providerColor(agent.provider)}33` : undefined,
              }}
              onClick={() => setSelectedAgent(isSelected ? null : agent.id)}
            >
              <div className="userver-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    padding: '2px 6px', borderRadius: 4,
                    background: 'rgba(88,166,255,0.15)', color: '#58a6ff',
                  }}>
                    #{agent.priority}
                  </span>
                  <h3 className="userver-heading" style={{ margin: 0 }}>{agent.name}</h3>
                </div>
                <span style={{
                  padding: '2px 8px', borderRadius: 999,
                  background: 'rgba(0,0,0,0.3)', color: providerColor(agent.provider),
                }}>
                  {agent.provider.toUpperCase()}
                </span>
              </div>

              <div className="userver-card-content">
                <p className="userver-text" style={{ margin: '0 0 8px' }}>{agent.description}</p>

                {/* Model assignment */}
                <div style={{
                  padding: 6, borderRadius: 4, marginBottom: 8,
                  background: 'var(--pico-card-sectioning-background-color, #1c2128)',
                }}>
                  <span style={{ color: '#58a6ff', display: 'block', marginBottom: 2 }}>Model</span>
                  <code style={{ wordBreak: 'break-all' }}>{agent.model}</code>
                </div>

                {/* Capabilities */}
                <div style={{ marginBottom: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {agent.capabilities.map(cap => (
                    <span key={cap} style={{
                      padding: '1px 6px', borderRadius: 999,
                      background: 'rgba(88,166,255,0.15)', color: '#58a6ff',
                    }}>
                      {cap}
                    </span>
                  ))}
                </div>

                {/* Stats row */}
                <div className="userver-service-details" style={{ gap: 12 }}>
                  <span>Cost/task: <strong>${agent.cost_per_task.toFixed(4)}</strong></span>
                  <span>Timeout: <strong>{agent.timeout}s</strong></span>
                </div>
              </div>

              {/* Expanded description */}
              {isSelected && (
                <div className="userver-card-content" style={{ paddingTop: 0, color: 'var(--pico-muted-color, #8b949e)' }}>
                  <hr style={{ border: 'none', borderTop: '1px solid var(--pico-border-color, #30363d)', margin: '8px 0' }} />
                  <p className="userver-text" style={{ margin: 0 }}>{agent.description}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Task routing info card */}
      <div className="userver-card" style={{ marginTop: 16, borderLeft: '3px solid #58a6ff', background: 'rgba(88,166,255,0.04)' }}>
        <div className="userver-card-header">
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Icon name="alt_route" size={16} />
            Task Routing
          </h3>
        </div>
        <div className="userver-card-content">
          <p className="userver-text" style={{ margin: 0 }}>
            Tasks are automatically routed to the most appropriate agent based on task type and complexity.
            Click an agent card to view its full configuration.
          </p>
        </div>
      </div>
    </div>
  )
}