/* ═══════════════════════════════════════════════════════════════════
   AgentsPanel — Specialized Agent Configuration Dashboard
   ═══════════════════════════════════════════════════════════════════
   Shows:
   - Configured specialized agents
   - Model assignments per agent
   - Capabilities and cost tracking
   - Task routing visualization
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

interface AgentStats {
  agent_id: string
  routed: number
  success: number
  error: number
  avg_cost: number
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
      case 'ollama':
        return '#58a6ff'
      case 'openrouter':
        return '#3fb950'
      case 'openai':
        return '#79c0ff'
      default:
        return '#8b949e'
    }
  }

  return (
    <div style={{ padding: '16px', height: '100%', overflow: 'auto' }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Icon name="smart_toy" size={20} />
          <h2 style={{ margin: 0 }}>Specialized Agents</h2>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--pico-muted-color, #8b949e)', margin: 0 }}>
          Configured agents by specialization with model assignments
        </p>
      </div>

      {loading && <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Loading...</p>}

      {agents.length === 0 ? (
        <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>No agents configured.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {agents.sort((a, b) => a.priority - b.priority).map(agent => (
            <div
              key={agent.id}
              style={{
                padding: 12,
                borderRadius: 6,
                border: selectedAgent === agent.id ? '2px solid #58a6ff' : '1px solid var(--pico-form-element-border-color, #30363d)',
                background: 'var(--pico-card-sectioning-background-color, #1c2128)',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                <div style={{ flex: 1 }}>
                  <h4 style={{ margin: '0 0 4px' }}>
                    #{agent.priority} {agent.name}
                  </h4>
                  <p style={{ margin: '0 0 4px', fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>
                    {agent.description}
                  </p>
                </div>
                <span
                  style={{
                    fontSize: '10px',
                    padding: '3px 8px',
                    borderRadius: 999,
                    background: 'rgba(0,0,0,0.3)',
                    color: providerColor(agent.provider),
                  }}
                >
                  {agent.provider.toUpperCase()}
                </span>
              </div>

              {/* Model Assignment */}
              <div
                style={{
                  padding: 8,
                  borderRadius: 4,
                  background: 'rgba(0,0,0,0.2)',
                  marginBottom: 8,
                }}
              >
                <p style={{ margin: '0 0 4px', fontSize: '10px', fontWeight: 'bold', color: '#58a6ff' }}>Model</p>
                <code
                  style={{
                    fontSize: '11px',
                    fontFamily: 'monospace',
                    color: 'var(--pico-color, #c9d1d9)',
                    wordBreak: 'break-all',
                  }}
                >
                  {agent.model}
                </code>
              </div>

              {/* Capabilities */}
              <div style={{ marginBottom: 8 }}>
                <p style={{ margin: '0 0 4px', fontSize: '10px', fontWeight: 'bold' }}>Capabilities</p>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {agent.capabilities.map(cap => (
                    <span
                      key={cap}
                      style={{
                        fontSize: '9px',
                        padding: '2px 6px',
                        borderRadius: 999,
                        background: 'rgba(88, 166, 255, 0.2)',
                        color: '#58a6ff',
                      }}
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>

              {/* Stats */}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--pico-muted-color, #8b949e)' }}>
                <span>Cost/task: ${agent.cost_per_task.toFixed(4)}</span>
                <span>Timeout: {agent.timeout}s</span>
              </div>

              {/* Expanded Details */}
              {selectedAgent === agent.id && (
                <div
                  style={{
                    marginTop: 12,
                    paddingTop: 12,
                    borderTop: '1px solid var(--pico-form-element-border-color, #30363d)',
                    fontSize: '11px',
                  }}
                >
                  <p style={{ margin: '0 0 8px', fontWeight: 'bold' }}>Description</p>
                  <p
                    style={{
                      margin: 0,
                      padding: 8,
                      borderRadius: 4,
                      background: 'rgba(0,0,0,0.2)',
                      fontSize: '10px',
                      lineHeight: 1.4,
                      color: 'var(--pico-color, #c9d1d9)',
                    }}
                  >
                    {agent.description}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <button
        onClick={() => void loadAgents()}
        disabled={loading}
        style={{
          marginTop: 16,
          padding: '8px 16px',
          fontSize: '12px',
          borderRadius: 4,
          border: '1px solid var(--pico-form-element-border-color, #30363d)',
          background: 'var(--pico-card-sectioning-background-color, #1c2128)',
          color: 'var(--pico-color, #c9d1d9)',
          cursor: 'pointer',
        }}
      >
        {loading ? 'Refreshing...' : 'Refresh'}
      </button>

      <div
        style={{
          marginTop: 24,
          padding: 12,
          borderRadius: 6,
          border: '1px solid var(--pico-form-element-border-color, #30363d)',
          background: 'rgba(88, 166, 255, 0.05)',
          fontSize: '11px',
          color: 'var(--pico-muted-color, #8b949e)',
        }}
      >
        <p style={{ margin: '0 0 4px', fontWeight: 'bold' }}>Task Routing</p>
        <p style={{ margin: 0 }}>
          Tasks are automatically routed to the most appropriate agent based on task type and complexity. Click an agent to view its
          full configuration.
        </p>
      </div>
    </div>
  )
}
