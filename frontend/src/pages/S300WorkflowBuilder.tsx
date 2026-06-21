/* ═══════════════════════════════════════════════════════════════════
   S300WorkflowBuilder — Workflow Builder System Page
   ═══════════════════════════════════════════════════════════════════
   S300: Media — Workflow Builder
   ═══════════════════════════════════════════════════════════════════ */
import React, { useEffect, useState } from 'react'
import USystemPage from '../components/uSystemPage'

const SNACKBAR_API = 'http://localhost:8484'

type WorkflowBoard = {
  name: string
  path: string
  count: number
  items: string[]
}

type WorkflowJob = {
  skill_id: string
  time?: string
  last_run?: string | null
  last_result?: { success?: boolean; timestamp?: string } | null
}

type WorkflowStatus = {
  engine: {
    name: string
    role: string
    command: string
    bind: string
    access: string
    isolation: string
    review_loop: string
    automation: string[]
  }
  guardrails: string[]
  task_markdown: {
    tasker_dir: string
    exists: boolean
    boards: WorkflowBoard[]
    count: number
    total_items: number
  }
  maintenance: {
    status: string
    endpoint: string
    jobs: WorkflowJob[]
  }
  next_actions: string[]
}

export default function S300WorkflowBuilder() {
  const [status, setStatus] = useState<WorkflowStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    async function loadWorkflowStatus() {
      try {
        setLoading(true)
        const res = await fetch(`${SNACKBAR_API}/api/system/workflow`, {
          signal: AbortSignal.timeout(2500),
        })
        if (!res.ok) {
          throw new Error(`workflow status request failed (${res.status})`)
        }
        const data = await res.json()
        if (active) {
          setStatus(data)
          setError(null)
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unable to load workflow status')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    loadWorkflowStatus()
    return () => {
      active = false
    }
  }, [])

  const boardCount = status?.task_markdown.count ?? 0
  const totalTasks = status?.task_markdown.total_items ?? 0
  const jobs = status?.maintenance.jobs ?? []

  return (
    <USystemPage
      page={300}
      title="Workflow Builder"
      subtitle="Cline Kanban orchestration with Markdown-first task flow"
      headerExtra={
        <button className="secondary" onClick={() => window.location.reload()}>
          Refresh
        </button>
      }
    >
      <div className="nestframe-grid">
        <article>
          <header>
            <strong>⚡ Core Workflow Engine</strong>
          </header>
          <p>
            {status?.engine.role || 'Local workflow surface for agent orchestration and task execution.'}
          </p>
          <ul>
            <li><strong>Engine:</strong> {status?.engine.name || 'Loading...'}</li>
            <li><strong>Launch:</strong> {status?.engine.command || 'npx kanban'}</li>
            <li><strong>Bind:</strong> {status?.engine.bind || '127.0.0.1:3484'}</li>
            <li><strong>Isolation:</strong> {status?.engine.isolation || 'Ephemeral worktrees'}</li>
          </ul>
          <footer>
            <small>{status?.engine.access || 'localhost-only'}</small>
          </footer>
        </article>

        <article>
          <header>
            <strong>🧱 Markdown Task Substrate</strong>
          </header>
          <p>Repo-adjacent `.tasker/` boards exported from AppFlowy/local workflow rows.</p>
          <ul>
            <li><strong>Boards:</strong> {boardCount}</li>
            <li><strong>Total Tasks:</strong> {totalTasks}</li>
            <li><strong>Path:</strong> {status?.task_markdown.tasker_dir || '.tasker'}</li>
          </ul>
          <footer>
            <small>{status?.task_markdown.exists ? 'Markdown boards detected' : 'Tasker directory not created yet'}</small>
          </footer>
        </article>

        <article>
          <header>
            <strong>🔐 Guardrails</strong>
          </header>
          <p>Lock the developer workflow to a controlled local environment and avoid public dev creep.</p>
          <ul>
            {(status?.guardrails || []).slice(0, 4).map((rule) => (
              <li key={rule}>{rule}</li>
            ))}
          </ul>
        </article>

        <article>
          <header>
            <strong>🌙 Overnight Orchestration</strong>
          </header>
          <p>Maintenance chain status from backup to vault sync to brain sync.</p>
          <ul>
            {jobs.length > 0 ? jobs.slice(0, 4).map((job) => (
              <li key={job.skill_id}>
                <strong>{job.skill_id}</strong>{' '}
                <small>{job.time || 'scheduled'} · last {job.last_run || 'never'}</small>
              </li>
            )) : <li>No scheduler data available</li>}
          </ul>
          <footer>
            <small>{status?.maintenance.endpoint || '/api/system/maintenance'}</small>
          </footer>
        </article>

        <article>
          <header>
            <strong>🗂️ Boards</strong>
          </header>
          {status?.task_markdown.boards?.length ? (
            <ul>
              {status.task_markdown.boards.map((board) => (
                <li key={board.name}>
                  <strong>{board.name}</strong> — {board.count} items
                </li>
              ))}
            </ul>
          ) : (
            <p>No `.tasker` boards yet. Run `tasker_sync` or the CLI exporter to populate them.</p>
          )}
        </article>

        <article>
          <header>
            <strong>🔄 Developer Loop</strong>
          </header>
          <p>Cline Kanban can sit above this stack as the visual orchestration layer while task state remains readable in Git.</p>
          <ul>
            {(status?.engine.automation || []).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article>
          <header>
            <strong>➡️ Next Wiring</strong>
          </header>
          <ul>
            {(status?.next_actions || []).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>

      {loading && <p>Loading workflow status...</p>}
      {error && <p style={{ color: 'var(--pico-del-color, #f85149)' }}>Workflow status error: {error}</p>}
    </USystemPage>
  )
}
