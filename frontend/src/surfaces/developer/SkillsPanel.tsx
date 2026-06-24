/* ═══════════════════════════════════════════════════════════════════
   SkillsPanel — Developer Skills Runner
   Lists all available skills from the backend API and provides
   a run button per skill with inline output viewer.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useCallback } from 'react'
import { Icon } from '../../components/Icon'

interface SkillInfo {
  id: string
  name: string
  description: string
  category: string
  timeout: number
}

interface SkillOutput {
  loading: boolean
  data: string | null
  error: string | null
  skillId: string | null
}

const SNACKBAR_API = 'http://localhost:8484'

export function SkillsPanel() {
  const [skills, setSkills] = useState<SkillInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [output, setOutput] = useState<SkillOutput>({
    loading: false,
    data: null,
    error: null,
    skillId: null,
  })
  const [paramInputs, setParamInputs] = useState<Record<string, string>>({})

  useEffect(() => {
    async function fetchSkills() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${SNACKBAR_API}/api/skills`, {
          signal: AbortSignal.timeout(4000),
        })
        if (!res.ok) throw new Error(`Skills API returned ${res.status}`)
        const data = await res.json()
        setSkills(data.skills || [])
      } catch (err: any) {
        setError(err?.message || 'Failed to load skills')
        // Fallback sample skills for offline/development
        setSkills([
          { id: 'usx-standard', name: 'USX Standard Builder', description: 'Audit CSS files for USX compliance and consolidate styling', category: 'developer', timeout: 120 },
          { id: 'surface-repair', name: 'Surface Repair', description: 'Repair surface configuration files', category: 'developer', timeout: 60 },
          { id: 'vault-sync', name: 'Vault Sync', description: 'Sync vault with AppFlowy', category: 'maintenance', timeout: 60 },
          { id: 'git-maintenance', name: 'Git Maintenance', description: 'Git housekeeping and branch cleanup', category: 'developer', timeout: 60 },
          { id: 'clipboard-maintenance', name: 'Clipboard Maintenance', description: 'Clean and organize clipboard entries', category: 'maintenance', timeout: 30 },
        ])
      } finally {
        setLoading(false)
      }
    }
    void fetchSkills()
  }, [])

  const handleRun = useCallback(async (skill: SkillInfo) => {
    setOutput({ loading: true, data: null, error: null, skillId: skill.id })
    try {
      const body: Record<string, any> = {}
      if (skill.id === 'usx-standard') {
        body.action = paramInputs[`${skill.id}-action`] || 'audit'
        body.target = paramInputs[`${skill.id}-target`] || ''
      }
      const res = await fetch(`${SNACKBAR_API}/api/skills/${skill.id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(skill.timeout * 1000 + 5000),
      })
      const result = await res.json()
      if (!res.ok) {
        setOutput({ loading: false, data: null, error: result.error || `HTTP ${res.status}`, skillId: skill.id })
        return
      }
      // Format output nicely
      const formatted = JSON.stringify(result, null, 2)
      setOutput({ loading: false, data: formatted, error: null, skillId: skill.id })
    } catch (err: any) {
      setOutput({ loading: false, data: null, error: err?.message || 'Skill execution failed', skillId: skill.id })
    }
  }, [paramInputs])

  const handleCloseOutput = useCallback(() => {
    setOutput({ loading: false, data: null, error: null, skillId: null })
  }, [])

  const categories = [...new Set(skills.map(s => s.category))]

  return (
    <div className="developer-panel">
      <div className="developer-panel-header">
        <h3 className="developer-panel-title">Skill Runner</h3>
        <span className="developer-panel-count">{skills.length} skills</span>
      </div>

      {error && (
        <div className="developer-skill-card" style={{ borderLeft: '3px solid #f85149', padding: 12 }}>
          <span style={{ color: '#f85149', fontSize: 12 }}>{error}</span>
        </div>
      )}

      {loading && skills.length === 0 && (
        <div className="developer-panel-count">Loading skills...</div>
      )}

      {categories.map(cat => (
        <div key={cat} style={{ marginBottom: 16 }}>
          <h4 style={{ textTransform: 'capitalize', margin: '0 0 8px', color: 'var(--pico-muted-color, #8b949e)' }}>
            <Icon name="extension" size={14} /> {cat}
          </h4>
          <div className="developer-skills-grid">
            {skills.filter(s => s.category === cat).map(skill => (
              <div key={skill.id} className="developer-skill-card">
                <div className="developer-skill-card-header">
                  <span className="developer-skill-name">{skill.name}</span>
                  <span className="developer-skill-id">{skill.id}</span>
                </div>
                <p className="developer-skill-desc">{skill.description}</p>

                {/* Skill-specific params */}
                {skill.id === 'usx-standard' && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <select
                      className="developer-search-input"
                      style={{ width: 'auto', flex: 1, minWidth: 100 }}
                      value={paramInputs[`${skill.id}-action`] || 'audit'}
                      onChange={e => setParamInputs(p => ({ ...p, [`${skill.id}-action`]: e.target.value }))}
                    >
                      <option value="audit">Audit</option>
                      <option value="report">Report</option>
                      <option value="consolidate">Consolidate</option>
                    </select>
                    <input
                      className="developer-search-input"
                      style={{ width: 'auto', flex: 1, minWidth: 80 }}
                      placeholder="Target (optional)"
                      value={paramInputs[`${skill.id}-target`] || ''}
                      onChange={e => setParamInputs(p => ({ ...p, [`${skill.id}-target`]: e.target.value }))}
                    />
                  </div>
                )}

                <button
                  className="developer-skill-run-btn"
                  onClick={() => handleRun(skill)}
                  disabled={output.loading && output.skillId === skill.id}
                >
                  {output.loading && output.skillId === skill.id ? 'Running...' : 'Run Skill'}
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Output Panel */}
      {output.data && output.skillId && (
        <div className="developer-skill-output">
          <div className="developer-skill-output-header">
            <span>Output: {skills.find(s => s.id === output.skillId)?.name || output.skillId}</span>
            <button className="developer-skill-output-close" onClick={handleCloseOutput}>
              <Icon name="close" size={14} />
            </button>
          </div>
          <pre className="developer-skill-output-text"><code>{output.data}</code></pre>
        </div>
      )}

      {output.error && output.skillId && (
        <div className="developer-skill-output" style={{ borderLeft: '3px solid #f85149' }}>
          <div className="developer-skill-output-header" style={{ color: '#f85149' }}>
            <span>Error: {skills.find(s => s.id === output.skillId)?.name || output.skillId}</span>
            <button className="developer-skill-output-close" onClick={handleCloseOutput}>
              <Icon name="close" size={14} />
            </button>
          </div>
          <pre className="developer-skill-output-text" style={{ color: '#f85149' }}><code>{output.error}</code></pre>
        </div>
      )}
    </div>
  )
}