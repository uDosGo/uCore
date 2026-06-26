import React, { useState, useEffect } from 'react'
import { Icon } from '../../components/Icon'

interface RoutingAnalytics {
  total_routed: number
  total_errors: number
  error_rate: number
  avg_cost_per_task: number
  total_cost_savings: number
  total_token_savings: number
  avg_latency_ms: number
  by_provider: Record<string, number>
  by_complexity: Record<string, number>
  recent_routes: Array<{
    task_id: string
    task_description: string
    complexity: string
    selected_provider: string
    selected_model: string
    estimated_cost: number
    estimated_tokens: number
    estimated_latency_ms: number
    timestamp: string
  }>
}

const SNACKBAR_API = 'http://localhost:8484'

export function RoutingAnalyticsPanel() {
  const [analytics, setAnalytics] = useState<RoutingAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchAnalytics() {
      try {
        const res = await fetch(`${SNACKBAR_API}/api/flow-router/analytics`, {
          signal: AbortSignal.timeout(3000),
        })
        if (!res.ok) throw new Error(`Analytics unavailable (${res.status})`)
        const data = await res.json()
        if (!cancelled) {
          setAnalytics(data)
          setError(null)
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message || 'Failed to load routing analytics')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchAnalytics()
    const interval = autoRefresh ? setInterval(fetchAnalytics, 5000) : undefined
    return () => {
      cancelled = true
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh])

  if (loading) {
    return (
      <div className="developer-panel">
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Flow-LLM Routing Analytics</h3>
          <span className="developer-panel-count">Loading...</span>
        </div>
      </div>
    )
  }

  if (error || !analytics) {
    return (
      <div className="developer-panel" style={{ border: '1px solid var(--pico-form-element-invalid-border-color, #f85149)' }}>
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Flow-LLM Routing Analytics</h3>
          <span className="developer-panel-count" style={{ color: 'var(--pico-form-element-invalid-border-color, #f85149)' }}>Error</span>
        </div>
        <div style={{ padding: '12px', color: 'var(--pico-form-element-invalid-border-color, #f85149)', fontSize: '12px' }}>
          {error || 'Routing service unavailable'}
        </div>
      </div>
    )
  }

  const errorRateColor = analytics.error_rate > 0.1 ? 'var(--pico-del-color, #f85149)' : 'var(--pico-ins-color, #3fb950)'
  const latencyColor = analytics.avg_latency_ms > 200 ? 'var(--pico-del-color, #f85149)' : 'var(--pico-ins-color, #3fb950)'

  return (
    <>
      {/* Summary Stats */}
      <div className="developer-panel">
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Flow-LLM Routing Analytics</h3>
          <label style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
            <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} style={{ margin: 0 }} />
            Auto-refresh
          </label>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, padding: '12px' }}>
          {/* Total Routed */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Total Routed</span>
            <span style={{ fontSize: '18px', fontWeight: 'bold', fontFamily: 'monospace' }}>{analytics.total_routed}</span>
          </div>

          {/* Error Rate */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Error Rate</span>
            <span style={{ fontSize: '18px', fontWeight: 'bold', fontFamily: 'monospace', color: errorRateColor }}>
              {(analytics.error_rate * 100).toFixed(1)}%
            </span>
          </div>

          {/* Avg Latency */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Avg Latency</span>
            <span style={{ fontSize: '18px', fontWeight: 'bold', fontFamily: 'monospace', color: latencyColor }}>
              {analytics.avg_latency_ms.toFixed(0)}ms
            </span>
          </div>

          {/* Cost per Task */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Avg Cost/Task</span>
            <span style={{ fontSize: '14px', fontFamily: 'monospace' }}>${analytics.avg_cost_per_task.toFixed(4)}</span>
          </div>

          {/* Cost Savings */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Cost Savings</span>
            <span style={{ fontSize: '14px', fontFamily: 'monospace', color: 'var(--pico-ins-color, #3fb950)' }}>
              ${analytics.total_cost_savings.toFixed(2)}
            </span>
          </div>

          {/* Token Savings */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>Token Savings</span>
            <span style={{ fontSize: '14px', fontFamily: 'monospace', color: 'var(--pico-ins-color, #3fb950)' }}>
              {analytics.total_token_savings.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Provider Distribution */}
      <div className="developer-panel" style={{ marginTop: '16px' }}>
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Provider Distribution</h3>
          <span className="developer-panel-count">{Object.keys(analytics.by_provider).length} providers</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '12px' }}>
          {Object.entries(analytics.by_provider).map(([provider, count]) => {
            const percentage = analytics.total_routed > 0 ? (count / analytics.total_routed) * 100 : 0
            const providerColor =
              provider === 'ollama' ? 'var(--pico-primary, #58a6ff)' :
              provider === 'openrouter' ? 'var(--pico-ins-color, #3fb950)' :
              'var(--pico-muted-color, #8b949e)'

            return (
              <div key={provider} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ minWidth: 100, fontSize: '12px', color: providerColor, fontWeight: 'bold' }}>
                  {provider.toUpperCase()}
                </div>
                <div
                  style={{
                    flex: 1,
                    height: 16,
                    background: 'var(--pico-border-color, #30363d)',
                    borderRadius: 2,
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      background: providerColor,
                      width: `${percentage}%`,
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
                <div style={{ minWidth: 80, textAlign: 'right', fontSize: '11px', fontFamily: 'monospace', color: 'var(--pico-muted-color, #8b949e)' }}>
                  {count} ({percentage.toFixed(1)}%)
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Complexity Distribution */}
      <div className="developer-panel" style={{ marginTop: '16px' }}>
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Complexity Distribution</h3>
          <span className="developer-panel-count">{Object.keys(analytics.by_complexity).length} levels</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '12px' }}>
          {Object.entries(analytics.by_complexity).map(([complexity, count]) => {
            const percentage = analytics.total_routed > 0 ? (count / analytics.total_routed) * 100 : 0
            const complexityColor =
              complexity === 'simple' ? 'var(--pico-ins-color, #3fb950)' :
              complexity === 'medium' ? 'var(--pico-warning-color, #d29922)' :
              'var(--pico-del-color, #f85149)'

            return (
              <div key={complexity} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ minWidth: 100, fontSize: '12px', color: complexityColor, fontWeight: 'bold', textTransform: 'capitalize' }}>
                  {complexity}
                </div>
                <div
                  style={{
                    flex: 1,
                    height: 16,
                    background: 'var(--pico-border-color, #30363d)',
                    borderRadius: 2,
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      background: complexityColor,
                      width: `${percentage}%`,
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
                <div style={{ minWidth: 80, textAlign: 'right', fontSize: '11px', fontFamily: 'monospace', color: 'var(--pico-muted-color, #8b949e)' }}>
                  {count} ({percentage.toFixed(1)}%)
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Recent Routes */}
      <div className="developer-panel" style={{ marginTop: '16px' }}>
        <div className="developer-panel-header">
          <h3 className="developer-panel-title">Recent Routes</h3>
          <span className="developer-panel-count">{analytics.recent_routes.length}</span>
        </div>

        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {analytics.recent_routes.length === 0 ? (
            <div style={{ padding: '12px', color: 'var(--pico-muted-color, #8b949e)', fontSize: '12px' }}>
              No recent routes
            </div>
          ) : (
            analytics.recent_routes.map((route, i) => (
              <div
                key={i}
                style={{
                  padding: '10px 12px',
                  borderBottom: '1px solid var(--pico-border-color, #30363d)',
                  fontSize: '11px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ color: 'var(--pico-primary, #58a6ff)', fontWeight: 'bold', marginBottom: 4 }}>
                      {route.task_description.substring(0, 60)}
                      {route.task_description.length > 60 ? '...' : ''}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, color: 'var(--pico-muted-color, #8b949e)', fontSize: '10px', fontFamily: 'monospace' }}>
                      <span>Complexity: <strong style={{ color: 'inherit' }}>{route.complexity}</strong></span>
                      <span>Provider: <strong style={{ color: 'inherit' }}>{route.selected_provider}</strong></span>
                      <span>Cost: <strong style={{ color: 'var(--pico-ins-color, #3fb950)' }}>${route.estimated_cost.toFixed(4)}</strong></span>
                      <span>Latency: <strong style={{ color: 'inherit' }}>{route.estimated_latency_ms}ms</strong></span>
                      <span>Tokens: <strong style={{ color: 'inherit' }}>{route.estimated_tokens}</strong></span>
                      <span>Model: <strong style={{ color: 'inherit' }}>{route.selected_model.split('/').pop()}</strong></span>
                    </div>
                  </div>
                  <div style={{ whiteSpace: 'nowrap', color: 'var(--pico-muted-color, #8b949e)', fontSize: '10px' }}>
                    {new Date(route.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Info */}
      <div className="developer-panel" style={{ marginTop: '16px', background: 'var(--pico-code-background, #0d1117)', padding: '12px' }}>
        <div style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)', lineHeight: '1.6' }}>
          <p style={{ margin: '0 0 8px 0' }}>
            <strong>Flow-LLM Router</strong> intelligently selects the best provider/model for each task based on
            complexity, cost, context size, and risk level.
          </p>
          <p style={{ margin: '0 0 8px 0' }}>
            • <strong>Simple Tasks</strong>: Local Ollama (free, no latency)
          </p>
          <p style={{ margin: '0 0 8px 0' }}>
            • <strong>Medium Tasks</strong>: OpenRouter balance tier (cost-efficient)
          </p>
          <p style={{ margin: 0 }}>
            • <strong>Complex Tasks</strong>: Premium providers for reasoning and quality
          </p>
        </div>
      </div>
    </>
  )
}
