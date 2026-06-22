/* ═══════════════════════════════════════════════════════════════════
   S330MigrationDashboard — Consolidation Progress & Metrics
   ═══════════════════════════════════════════════════════════════════
   S330: Workflow — Migration & Consolidation Dashboard
   Shows: Import progress, index coverage, consolidation checklist
   ═══════════════════════════════════════════════════════════════════ */
import React, { useEffect, useState, useCallback } from 'react'
import USystemPage from '../components/uSystemPage'

const SNACKBAR_API = 'http://localhost:8484'

type ImportJob = {
  id: string
  status: 'queued' | 'in-progress' | 'completed' | 'error'
  progress: number
  message: string
  timestamp: string
}

type IndexMetric = {
  source: string
  expected: number
  indexed: number
  coverage_percent: number
}

type ConsolidationItem = {
  task: string
  completed: boolean
  category: 'docs' | 'repo' | 'ui' | 'integration'
  details?: string
}

export default function S330MigrationDashboard() {
  const [importJobs, setImportJobs] = useState<ImportJob[]>([])
  const [indexMetrics, setIndexMetrics] = useState<IndexMetric[]>([])
  const [consolidation, setConsolidation] = useState<ConsolidationItem[]>([
    { task: 'Migrate architecture docs to uDocs', completed: true, category: 'docs' },
    { task: 'Migrate API reference to uDocs', completed: true, category: 'docs' },
    { task: 'Migrate runbooks to uDocs', completed: true, category: 'docs' },
    { task: 'Link all repo READMEs to uDocs', completed: false, category: 'repo' },
    { task: 'Consolidate duplicate docs', completed: false, category: 'docs' },
    { task: 'Archive legacy docs with pointers', completed: false, category: 'docs' },
    { task: 'Wire S320 knowledge UI', completed: true, category: 'ui' },
    { task: 'Add S330 migration dashboard', completed: true, category: 'ui' },
    { task: 'Implement S300 board actions', completed: false, category: 'ui' },
    { task: 'Add task detail drawer', completed: false, category: 'ui' },
    { task: 'Integrate n8n workflows', completed: false, category: 'integration' },
    { task: 'Setup Firewatch MCP for browser', completed: false, category: 'integration' },
  ])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadImportStatus = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/import/status`, {
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        const data = await res.json()
        setImportJobs(data.jobs || [])
      }
    } catch (err) {
      // Endpoint may not exist yet - that's ok
      console.log('Import status endpoint not yet available')
    }
  }, [])

  const loadIndexMetrics = useCallback(async () => {
    try {
      const res = await fetch(`${SNACKBAR_API}/api/knowledge/index/coverage`, {
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        const data = await res.json()
        setIndexMetrics(data.coverage || [])
      }
    } catch (err) {
      console.log('Coverage endpoint not yet available')
    }
  }, [])

  const toggleConsolidationTask = useCallback((index: number) => {
    setConsolidation(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], completed: !updated[index].completed }
      return updated
    })
  }, [])

  useEffect(() => {
    setLoading(true)
    Promise.all([loadImportStatus(), loadIndexMetrics()]).finally(() => setLoading(false))
  }, [loadImportStatus, loadIndexMetrics])

  const completedConsolidation = consolidation.filter(item => item.completed).length
  const totalConsolidation = consolidation.length
  const consolidationPercent = (completedConsolidation / totalConsolidation) * 100

  const totalExpected = indexMetrics.reduce((sum, m) => sum + m.expected, 0)
  const totalIndexed = indexMetrics.reduce((sum, m) => sum + m.indexed, 0)
  const overallCoveragePercent = totalExpected > 0 ? (totalIndexed / totalExpected) * 100 : 0

  return (
    <USystemPage
      page={330}
      title="Migration & Consolidation"
      subtitle="Track import progress, index coverage, and consolidation checklist"
    >
      {error && (
        <div style={{ padding: 12, background: 'rgba(248, 81, 73, 0.1)', color: '#f85149', borderRadius: 6, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {loading ? (
        <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Loading dashboard...</p>
      ) : (
        <div className="nestframe-grid">
          {/* ─── Overall Progress ──────────────────────────────── */}
          <article style={{ gridColumn: 'span 2' }}>
            <header><strong>📊 Consolidation Progress</strong></header>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: 'var(--pico-primary, #58a6ff)' }}>
                  {completedConsolidation}/{totalConsolidation}
                </div>
                <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Tasks Completed</small>
              </div>
              <div>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#3fb950' }}>
                  {consolidationPercent.toFixed(0)}%
                </div>
                <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Overall Progress</small>
              </div>
              <div>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#a855f7' }}>
                  {totalIndexed}/{totalExpected}
                </div>
                <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>Documents Indexed</small>
              </div>
            </div>
            <div style={{
              width: '100%',
              height: 12,
              background: 'var(--pico-border-color, #30363d)',
              borderRadius: 6,
              overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                width: `${consolidationPercent}%`,
                background: 'linear-gradient(90deg, #58a6ff, #3fb950)',
                transition: 'width 0.3s ease',
              }} />
            </div>
          </article>

          {/* ─── Index Coverage ────────────────────────────────── */}
          <article style={{ gridColumn: 'span 2' }}>
            <header><strong>📑 Index Coverage by Source</strong></header>
            {indexMetrics.length === 0 ? (
              <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>No coverage data. Run import/sync first.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {indexMetrics.map((metric, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: '0.9rem' }}>
                      <strong>{metric.source}</strong>
                      <span style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
                        {metric.indexed} / {metric.expected}
                      </span>
                    </div>
                    <div style={{
                      width: '100%',
                      height: 8,
                      background: 'var(--pico-border-color, #30363d)',
                      borderRadius: 4,
                      overflow: 'hidden',
                    }}>
                      <div style={{
                        height: '100%',
                        width: `${Math.min(100, metric.coverage_percent)}%`,
                        background: metric.coverage_percent > 90 ? '#3fb950' : metric.coverage_percent > 50 ? '#d29922' : '#f85149',
                      }} />
                    </div>
                    <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
                      {metric.coverage_percent.toFixed(1)}% coverage
                    </small>
                  </div>
                ))}
              </div>
            )}
          </article>

          {/* ─── Import Jobs ─────────────────────────────────── */}
          <article>
            <header><strong>⏳ Recent Import Jobs</strong></header>
            {importJobs.length === 0 ? (
              <p style={{ color: 'var(--pico-muted-color, #8b949e)' }}>No recent jobs. Trigger an import to get started.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {importJobs.slice(-5).map((job, i) => (
                  <div key={i} style={{
                    padding: '8px 10px',
                    border: '1px solid var(--pico-border-color, #30363d)',
                    borderRadius: 4,
                    fontSize: '0.8rem',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <strong>{job.id.substring(0, 12)}...</strong>
                      <span style={{
                        fontSize: '0.75rem',
                        padding: '2px 6px',
                        borderRadius: 3,
                        background: job.status === 'completed' ? 'rgba(63, 185, 80, 0.1)' : job.status === 'error' ? 'rgba(248, 81, 73, 0.1)' : 'rgba(88, 166, 255, 0.1)',
                        color: job.status === 'completed' ? '#3fb950' : job.status === 'error' ? '#f85149' : '#58a6ff',
                      }}>
                        {job.status}
                      </span>
                    </div>
                    {job.progress > 0 && (
                      <div style={{
                        width: '100%',
                        height: 4,
                        background: 'var(--pico-border-color, #30363d)',
                        borderRadius: 2,
                        marginBottom: 4,
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${job.progress}%`,
                          background: '#58a6ff',
                        }} />
                      </div>
                    )}
                    <small style={{ color: 'var(--pico-muted-color, #8b949e)' }}>
                      {job.message}
                    </small>
                  </div>
                ))}
              </div>
            )}
          </article>

          {/* ─── Consolidation Checklist ──────────────────────── */}
          <article style={{ gridColumn: 'span 2' }}>
            <header><strong>✅ Consolidation Checklist</strong></header>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {consolidation.map((item, i) => (
                <label key={i} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 8px',
                  borderRadius: 4,
                  cursor: 'pointer',
                  background: item.completed ? 'rgba(63, 185, 80, 0.05)' : 'transparent',
                  fontSize: '0.9rem',
                }}>
                  <input
                    type="checkbox"
                    checked={item.completed}
                    onChange={() => toggleConsolidationTask(i)}
                    style={{ cursor: 'pointer' }}
                  />
                  <span style={{
                    textDecoration: item.completed ? 'line-through' : 'none',
                    color: item.completed ? 'var(--pico-muted-color, #8b949e)' : 'inherit',
                  }}>
                    {item.task}
                  </span>
                  <small style={{
                    marginLeft: 'auto',
                    fontSize: '0.75rem',
                    padding: '2px 6px',
                    background: item.category === 'docs' ? 'rgba(88, 166, 255, 0.1)' : item.category === 'repo' ? 'rgba(168, 85, 247, 0.1)' : item.category === 'ui' ? 'rgba(52, 211, 153, 0.1)' : 'rgba(250, 204, 21, 0.1)',
                    borderRadius: 3,
                    color: item.category === 'docs' ? '#58a6ff' : item.category === 'repo' ? '#a855f7' : item.category === 'ui' ? '#34d399' : '#facc15',
                  }}>
                    {item.category}
                  </small>
                </label>
              ))}
            </div>
            <footer>
              <small>{completedConsolidation} of {totalConsolidation} items completed</small>
            </footer>
          </article>
        </div>
      )}
    </USystemPage>
  )
}
