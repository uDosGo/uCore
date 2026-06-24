/* ═══════════════════════════════════════════════════════════════════
   SystemToolsSurface — Tools Registry (things that DO something)
   ═══════════════════════════════════════════════════════════════════
   Tools are actions/services/executables — NOT pages/routes/fallbacks.
   Pages go in the Pages tab. Tools go here.
   Pure Pico CSS classes — no inline styles for layout/typography.
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { Icon } from '../../components/Icon'
import '../../styles/hub/index.css'

interface Tool {
  id: string
  name: string
  description: string
  icon: string
  category: string
  status: 'active' | 'planned' | 'external'
  actionLabel: string
}

const TOOLS: Tool[] = [
  {
    id: 'mcp-bridge',
    name: 'MCP Bridge',
    description: 'Model Context Protocol bridge — connect external MCP tool servers and expose their tools to the system.',
    icon: 'bridge',
    category: 'Integration',
    status: 'active',
    actionLabel: 'Launch Bridge',
  },
  {
    id: 'task-scheduler',
    name: 'Task Scheduler',
    description: 'Schedule recurring tasks, cron jobs, and system maintenance routines.',
    icon: 'schedule',
    category: 'Automation',
    status: 'planned',
    actionLabel: 'Configure',
  },
  {
    id: 'data-importer',
    name: 'Data Importer',
    description: 'Import data from external sources — files, APIs, databases.',
    icon: 'upload',
    category: 'Data',
    status: 'planned',
    actionLabel: 'Import',
  },
  {
    id: 'batch-processor',
    name: 'Batch Processor',
    description: 'Process multiple items or files in parallel with configurable pipelines.',
    icon: 'settings_suggest',
    category: 'Processing',
    status: 'planned',
    actionLabel: 'Process',
  },
  {
    id: 'clipboard-sync',
    name: 'Clipboard Sync',
    description: 'Synchronize clipboard buffer across devices and surfaces.',
    icon: 'content_paste',
    category: 'Integration',
    status: 'active',
    actionLabel: 'Sync',
  },
  {
    id: 'vault-indexer',
    name: 'Vault Indexer',
    description: 'Index vault documents for semantic search and knowledge retrieval.',
    icon: 'folder_sync',
    category: 'Data',
    status: 'active',
    actionLabel: 'Index',
  },
  {
    id: 'secret-sync',
    name: 'Secret Sync',
    description: 'Sync secrets between encrypted store, .env files, and environment variables.',
    icon: 'key',
    category: 'Security',
    status: 'active',
    actionLabel: 'Sync Secrets',
  },
]

function ToolsPanel() {
  const categories = Array.from(new Set(TOOLS.map(t => t.category)))

  return (
    <article className="container-fluid" style={{ margin: '12px', maxWidth: '960px' }}>
      <header>
        <hgroup>
          <h5>System Tools</h5>
          <p style={{ margin: 0 }}>Active services and utilities — things that DO something</p>
        </hgroup>
      </header>

      {categories.map(category => (
        <div key={category} style={{ marginBottom: '16px' }}>
          <h6 style={{ margin: '0 0 8px 0' }}>{category}</h6>
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))' }}>
            {TOOLS.filter(t => t.category === category).map(tool => (
              <div
                key={tool.id}
                className="outline"
                role="button"
                style={{
                  padding: '12px',
                  textAlign: 'left',
                  cursor: 'default',
                  opacity: tool.status === 'active' ? 1 : 0.6,
                }}
              >
                <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                  <Icon name={tool.icon as any} size={20} />
                  <div>
                    <strong>{tool.name}</strong>
                    <br />
                    <small>{tool.description}</small>
                    <br />
                    <kbd style={{ marginTop: '6px', display: 'inline-block' }}>
                      {tool.status === 'active' ? tool.actionLabel : 'Coming soon'}
                    </kbd>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </article>
  )
}

function SystemPagesPanel() {
  return (
    <div className="container-fluid" style={{ padding: '16px', maxWidth: '960px' }}>
      <article>
        <header>
          <h5>System Pages Reference</h5>
        </header>
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '8px' }}>
          {[
            { range: 'S100-S199', label: 'Tools & asset creation' },
            { range: 'S200-S299', label: 'Content management' },
            { range: 'S300-S399', label: 'Workflow & orchestration' },
            { range: 'S400-S499', label: 'Integration & modules' },
            { range: 'S500-S599', label: 'Security & configuration' },
            { range: 'S600-S699', label: 'Learning & documentation' },
            { range: 'S700-S799', label: 'Advanced features' },
            { range: 'S800-S899', label: 'System status & diagnostics' },
            { range: 'P100-P999', label: 'Surface status & fallback' },
          ].map(item => (
            <div key={item.range} className="outline" style={{ padding: '10px', textAlign: 'center' }}>
              <kbd>{item.range}</kbd>
              <div style={{ marginTop: '4px' }}><small>{item.label}</small></div>
            </div>
          ))}
        </div>
      </article>
    </div>
  )
}

export { ToolsPanel, SystemPagesPanel }

export default function SystemToolsSurface() {
  return null
}