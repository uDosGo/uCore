/* ═══════════════════════════════════════════════════════════════════
   ModelsPanel — Ollama Model Management Dashboard
   ═══════════════════════════════════════════════════════════════════
   Shows:
   - Downloaded models with sizes
   - Available models to pull
   - Performance stats per model
   - Real-time Ollama health
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'

const SNACKBAR_API = 'http://localhost:8484'

interface OllamaModel {
  name: string
  size_gb: number
  modified_at: string
  digest: string
}

interface ModelPerformance {
  uses: number
  success_rate: number
  error_count: number
  avg_latency_ms: number
  last_used: string
}

interface OllamaStatus {
  online: boolean
  base_url?: string
  models: OllamaModel[]
  model_count: number
  error?: string
}

interface AvailableModel {
  name: string
  size_gb: number
  description: string
  capabilities: string[]
}

// ─── Roundtable Provider Config ───────────────────────────────────────
const ROUNDTABLE_PROVIDERS = [
  { id: 'openrouter', name: 'OpenRouter', icon: 'cloud', color: '#3fb950', desc: 'Multi-model API gateway — paid, wide selection' },
  { id: 'openai', name: 'OpenAI', icon: 'bolt', color: '#79c0ff', desc: 'GPT-4o, GPT-4, GPT-3.5 — paid, high quality' },
  { id: 'ollama', name: 'Ollama', icon: 'memory', color: '#58a6ff', desc: 'Local models — free, private, no internet needed' },
  { id: 'anthropic', name: 'Anthropic', icon: 'smart_toy', color: '#d29922', desc: 'Claude models — paid, reasoning-focused' },
]

const PRIORITY_PRESETS = [
  { label: 'Cost First', value: 'cost', desc: 'Prioritise cheapest providers (Ollama > OpenRouter > OpenAI)' },
  { label: 'Quality First', value: 'quality', desc: 'Prioritise best models (OpenAI > Anthropic > OpenRouter)' },
  { label: 'Balanced', value: 'balanced', desc: 'Default — mix of cost and quality based on task complexity' },
  { label: 'Local Only', value: 'local', desc: 'Ollama only — no external API calls, fully offline' },
]

export function ModelsPanel() {
  const [status, setStatus] = useState<OllamaStatus | null>(null)
  const [performance, setPerformance] = useState<Record<string, ModelPerformance>>({})
  const [available, setAvailable] = useState<AvailableModel[]>([])
  const [loading, setLoading] = useState(false)
  const [priorityMode, setPriorityMode] = useState('balanced')
  const [roundtableModal, setRoundtableModal] = useState(false)

  const loadModels = async () => {
    setLoading(true)
    try {
      const [statusRes, perfRes, availRes] = await Promise.all([
        fetch(`${SNACKBAR_API}/api/ollama/status`, { signal: AbortSignal.timeout(4000) }),
        fetch(`${SNACKBAR_API}/api/ollama/performance`, { signal: AbortSignal.timeout(4000) }),
        fetch(`${SNACKBAR_API}/api/ollama/models/available`, { signal: AbortSignal.timeout(4000) }),
      ])
      if (statusRes.ok) {
        const statusData = await statusRes.json()
        setStatus(statusData)
      }
      if (perfRes.ok) {
        const perfData = await perfRes.json()
        setPerformance(perfData.models || {})
      }
      if (availRes.ok) {
        const availData = await availRes.json()
        setAvailable(availData.recommended || [])
      }
    } catch (e) {
      console.error('Failed to load models:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadModels()
    const interval = setInterval(() => void loadModels(), 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '0 16px 16px' }}>
      {/* Toolbar header */}
      <div className="userver-toolbar" style={{ padding: '12px 0' }}>
        <div className="userver-toolbar-left">
          <h2 className="userver-heading" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name="memory" size={20} />
            Local Models
          </h2>
          <span className="userver-card-subtitle">
            {loading ? 'Loading…' : status ? `${status.model_count} models` : 'Ollama'}
          </span>
        </div>
        <div className="userver-toolbar-actions" style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          <button className="userver-action-btn" onClick={() => setRoundtableModal(true)} title="Roundtable provider config">
            <Icon name="tune" size={14} style={{ marginRight: 4 }} />
            Roundtable
          </button>
          <button className="userver-action-btn" onClick={() => void loadModels()} disabled={loading}>
            {loading ? '…' : <Icon name="refresh" size={14} />}
          </button>
        </div>
      </div>

      {loading && !status && (
        <p style={{ color: 'var(--pico-muted-color, #8b949e)', fontSize: 12 }}>Loading model data…</p>
      )}

      {status && (
        <>
          {/* ─── Roundtable Priority Switcher ─────────────────────── */}
          <div className="userver-card" style={{ marginBottom: 16 }}>
            <div className="userver-card-header">
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                <Icon name="alt_route" size={16} />
                Router Priority
              </h3>
              <span className="userver-card-subtitle">{PRIORITY_PRESETS.find(p => p.value === priorityMode)?.desc}</span>
            </div>
            <div className="userver-card-content" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {PRIORITY_PRESETS.map(p => (
                <button
                  key={p.value}
                  className="userver-action-btn"
                  onClick={() => setPriorityMode(p.value)}
                  style={{
                    borderColor: priorityMode === p.value ? '#58a6ff' : undefined,
                    color: priorityMode === p.value ? '#58a6ff' : undefined,
                    fontSize: 11,
                  }}
                  title={p.desc}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* ─── Ollama Status ────────────────────────────────────── */}
          <div className="userver-card" style={{ marginBottom: 16, borderLeft: `3px solid ${status.online ? '#3fb950' : '#f85149'}` }}>
            <div className="userver-card-header">
              <h3 style={{ margin: 0 }}>Instance Status</h3>
              <span style={{
                fontSize: 11, padding: '3px 10px', borderRadius: 999,
                background: status.online ? '#3fb950' : '#f85149',
                color: 'white', fontWeight: 600,
              }}>
                {status.online ? '✓ Online' : '✗ Offline'}
              </span>
            </div>
            <div className="userver-card-content">
              {status.online && (
                <div className="userver-service-details" style={{ gap: 16, fontSize: 12 }}>
                  <span>URL: <strong>{status.base_url || 'localhost:11434'}</strong></span>
                  <span>Models: <strong>{status.model_count} downloaded</strong></span>
                  <span>Status: <strong style={{ color: '#3fb950' }}>Healthy</strong></span>
                </div>
              )}
              {status.error && <p style={{ color: '#f85149', fontSize: 12, margin: '4px 0 0' }}>Error: {status.error}</p>}
            </div>
          </div>

          {/* ─── Downloaded Models ──────────────────────────────────── */}
          <div className="userver-card" style={{ marginBottom: 16 }}>
            <div className="userver-card-header">
              <h3 style={{ margin: 0 }}>Downloaded Models ({status.models.length})</h3>
            </div>
            <div className="userver-card-content">
              {status.models.length === 0 ? (
                <p style={{ color: 'var(--pico-muted-color, #8b949e)', fontSize: 12 }}>No models downloaded.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {status.models.map(model => {
                    const perf = performance[model.name]
                    return (
                      <div key={model.name} className="userver-service-row" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 4 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span className="userver-service-name" style={{ fontWeight: 600 }}>{model.name}</span>
                          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <span style={{ fontSize: 11, color: 'var(--pico-muted-color, #8b949e)' }}>{model.size_gb}GB</span>
                            <button style={{
                              padding: '2px 8px', fontSize: 10, borderRadius: 4,
                              border: '1px solid #8b949e', background: 'transparent', color: '#8b949e', cursor: 'pointer',
                            }}>Delete</button>
                          </div>
                        </div>
                        {perf && (
                          <div style={{ fontSize: 10, color: 'var(--pico-muted-color, #8b949e)', display: 'flex', gap: 12 }}>
                            <span>Uses: {perf.uses}</span>
                            <span>Success: {perf.success_rate}%</span>
                            <span>Latency: {perf.avg_latency_ms}ms</span>
                            {perf.last_used && <span>Last: {new Date(perf.last_used).toLocaleTimeString()}</span>}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* ─── Available Models ──────────────────────────────────── */}
          <div className="userver-card" style={{ marginBottom: 16 }}>
            <div className="userver-card-header">
              <h3 style={{ margin: 0 }}>Available to Pull ({available.length})</h3>
            </div>
            <div className="userver-card-content">
              {available.length === 0 ? (
                <p style={{ color: 'var(--pico-muted-color, #8b949e)', fontSize: 12 }}>No models available.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {available.map(model => (
                    <div key={model.name} className="userver-service-row" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 4 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <span style={{ fontWeight: 600, fontSize: 13 }}>{model.name}</span>
                          <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--pico-muted-color, #8b949e)' }}>{model.size_gb}GB</span>
                        </div>
                        <button style={{
                          padding: '4px 12px', fontSize: 11, borderRadius: 4,
                          border: 'none', background: '#58a6ff', color: 'white', cursor: 'pointer', fontWeight: 600,
                        }}>Pull</button>
                      </div>
                      <p style={{ margin: 0, fontSize: 11 }}>{model.description}</p>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {model.capabilities.map(cap => (
                          <span key={cap} style={{
                            fontSize: 9, padding: '1px 6px', borderRadius: 999,
                            background: 'rgba(88,166,255,0.15)', color: '#58a6ff',
                          }}>{cap}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* ─── Roundtable Config Modal ─────────────────────────────── */}
      {roundtableModal && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 2000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(2px)',
        }} onClick={() => setRoundtableModal(false)}>
          <div className="userver-card" style={{
            width: 480, maxHeight: '80vh', overflow: 'auto',
            margin: 0, border: '1px solid var(--pico-primary, #58a6ff)',
          }} onClick={e => e.stopPropagation()}>
            <div className="userver-card-header">
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Icon name="tune" size={18} />
                Roundtable Provider Config
              </h3>
              <button className="userver-action-btn" onClick={() => setRoundtableModal(false)} style={{ fontSize: 11 }}>Close</button>
            </div>
            <div className="userver-card-content" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <p className="userver-text" style={{ fontSize: 12, margin: 0 }}>
                Configure which providers are available to the model router. Toggle each provider on/off and set priority.
              </p>
              {ROUNDTABLE_PROVIDERS.map(p => (
                <div key={p.id} className="userver-service-row" style={{ borderLeft: `3px solid ${p.color}`, paddingLeft: 8 }}>
                  <div className="userver-service-info">
                    <span className="userver-service-name" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Icon name={p.icon} size={16} style={{ color: p.color }} />
                      {p.name}
                    </span>
                    <span className="userver-service-desc">{p.desc}</span>
                  </div>
                  <div className="userver-service-meta" style={{ gap: 8 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}>
                      <input type="checkbox" defaultChecked style={{ accentColor: p.color }} />
                      Enable
                    </label>
                  </div>
                </div>
              ))}
              <div style={{ marginTop: 8, padding: 8, borderRadius: 4, background: 'rgba(88,166,255,0.06)', fontSize: 11 }}>
                <p style={{ margin: 0, color: 'var(--pico-muted-color, #8b949e)' }}>
                  Provider config is stored client-side. Future: persist via <code>/api/config/providers</code>.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
