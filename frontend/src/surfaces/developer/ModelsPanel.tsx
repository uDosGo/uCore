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

export function ModelsPanel() {
  const [status, setStatus] = useState<OllamaStatus | null>(null)
  const [performance, setPerformance] = useState<Record<string, ModelPerformance>>({})
  const [available, setAvailable] = useState<AvailableModel[]>([])
  const [loading, setLoading] = useState(false)

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
    <div style={{ padding: '16px', height: '100%', overflow: 'auto' }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Icon name="memory" size={20} />
          <h2 style={{ margin: 0 }}>Ollama Model Manager</h2>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--pico-muted-color, #8b949e)', margin: 0 }}>
          Local model library management and performance monitoring
        </p>
      </div>

      {loading && <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Loading...</p>}

      {status && (
        <>
          {/* Status Header */}
          <div
            style={{
              padding: 12,
              borderRadius: 6,
              border: '1px solid var(--pico-form-element-border-color, #30363d)',
              background: 'var(--pico-card-sectioning-background-color, #1c2128)',
              marginBottom: 16,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h3 style={{ margin: 0 }}>Instance Status</h3>
              <span
                style={{
                  fontSize: '12px',
                  padding: '4px 12px',
                  borderRadius: 999,
                  background: status.online ? '#3fb950' : '#f85149',
                  color: 'white',
                  fontWeight: 'bold',
                }}
              >
                {status.online ? '✓ Online' : '✗ Offline'}
              </span>
            </div>
            {status.online && (
              <>
                <p style={{ margin: '0 0 4px', fontSize: '12px' }}>
                  <strong>URL:</strong> {status.base_url || 'localhost:11434'}
                </p>
                <p style={{ margin: 0, fontSize: '12px' }}>
                  <strong>Models:</strong> {status.model_count} downloaded
                </p>
              </>
            )}
            {status.error && (
              <p style={{ margin: 0, fontSize: '12px', color: '#f85149' }}>Error: {status.error}</p>
            )}
          </div>

          {/* Downloaded Models */}
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ marginBottom: 12 }}>Downloaded Models ({status.models.length})</h3>
            {status.models.length === 0 ? (
              <p style={{ color: 'var(--pico-muted-color, #8b949e)', fontSize: '12px' }}>No models downloaded.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {status.models.map(model => {
                  const perf = performance[model.name]
                  return (
                    <div
                      key={model.name}
                      style={{
                        padding: 12,
                        borderRadius: 6,
                        border: '1px solid var(--pico-form-element-border-color, #30363d)',
                        background: 'var(--pico-card-sectioning-background-color, #1c2128)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                        <div>
                          <h4 style={{ margin: '0 0 4px' }}>{model.name}</h4>
                          <p style={{ margin: 0, fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>
                            {model.size_gb}GB
                          </p>
                        </div>
                        <button
                          style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                            borderRadius: 4,
                            border: '1px solid #8b949e',
                            background: 'transparent',
                            color: '#8b949e',
                            cursor: 'pointer',
                          }}
                        >
                          Delete
                        </button>
                      </div>
                      {perf && (
                        <div style={{ fontSize: '10px', color: 'var(--pico-muted-color, #8b949e)' }}>
                          <p style={{ margin: '2px 0' }}>Uses: {perf.uses} | Success: {perf.success_rate}%</p>
                          <p style={{ margin: '2px 0' }}>Avg latency: {perf.avg_latency_ms}ms | Errors: {perf.error_count}</p>
                          {perf.last_used && (
                            <p style={{ margin: '2px 0' }}>Last used: {new Date(perf.last_used).toLocaleTimeString()}</p>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Available Models */}
          <div>
            <h3 style={{ marginBottom: 12 }}>Available to Pull ({available.length})</h3>
            {available.length === 0 ? (
              <p style={{ color: 'var(--pico-muted-color, #8b949e)', fontSize: '12px' }}>No models available.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {available.map(model => (
                  <div
                    key={model.name}
                    style={{
                      padding: 12,
                      borderRadius: 6,
                      border: '1px solid var(--pico-form-element-border-color, #30363d)',
                      background: 'rgba(0,0,0,0.1)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                      <div>
                        <h4 style={{ margin: '0 0 4px' }}>{model.name}</h4>
                        <p style={{ margin: '0 0 4px', fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>
                          {model.size_gb}GB
                        </p>
                        <p style={{ margin: 0, fontSize: '11px' }}>{model.description}</p>
                      </div>
                      <button
                        style={{
                          padding: '6px 12px',
                          fontSize: '11px',
                          borderRadius: 4,
                          border: 'none',
                          background: '#58a6ff',
                          color: 'white',
                          cursor: 'pointer',
                          fontWeight: 'bold',
                        }}
                      >
                        Pull
                      </button>
                    </div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                      {model.capabilities.map(cap => (
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
                ))}
              </div>
            )}
          </div>
        </>
      )}

      <button
        onClick={() => void loadModels()}
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
    </div>
  )
}
