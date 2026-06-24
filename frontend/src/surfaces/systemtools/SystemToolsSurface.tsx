/* ═══════════════════════════════════════════════════════════════════
   SystemToolsSurface — Services + S-Page Tool panels
   ═══════════════════════════════════════════════════════════════════
   ServicesPanel: Non-S-page services (MCP Bridge, Vault Indexer, etc.)
   SPageToolsPanel: S-page tools that DO something (S101, S100, S300-)
   Pure Pico CSS classes.
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon } from '../../components/Icon'
import '../../styles/hub/index.css'

interface ServiceEntry {
  id: string
  name: string
  description: string
  icon: string
  category: string
  status: 'active' | 'planned'
  actionLabel: string
}

const SERVICES: ServiceEntry[] = [
  { id: 'mcp-bridge', name: 'MCP Bridge', description: 'Model Context Protocol bridge — connect external MCP tool servers.', icon: 'hub', category: 'Integration', status: 'active', actionLabel: 'Launch Bridge' },
  { id: 'task-scheduler', name: 'Task Scheduler', description: 'Schedule recurring tasks, cron jobs, and maintenance routines.', icon: 'schedule', category: 'Automation', status: 'planned', actionLabel: 'Configure' },
  { id: 'data-importer', name: 'Data Importer', description: 'Import data from external sources — files, APIs, databases.', icon: 'upload', category: 'Data', status: 'planned', actionLabel: 'Import' },
  { id: 'batch-processor', name: 'Batch Processor', description: 'Process multiple items or files in parallel with pipelines.', icon: 'settings_suggest', category: 'Processing', status: 'planned', actionLabel: 'Process' },
  { id: 'clipboard-sync', name: 'Clipboard Sync', description: 'Synchronize clipboard buffer across devices and surfaces.', icon: 'content_paste', category: 'Integration', status: 'active', actionLabel: 'Sync' },
  { id: 'vault-indexer', name: 'Vault Indexer', description: 'Index vault documents for semantic search and knowledge retrieval.', icon: 'sync', category: 'Data', status: 'active', actionLabel: 'Index' },
  { id: 'secret-sync', name: 'Secret Sync', description: 'Sync secrets between encrypted store, .env files, and environment variables.', icon: 'key', category: 'Security', status: 'active', actionLabel: 'Sync Secrets' },
]

interface SPageTool {
  id: string
  name: string
  description: string
  icon: string
  category: string
  route: string
  status: 'built' | 'stub'
}

const S_PAGE_TOOLS: SPageTool[] = [
  { id: 's101', name: 'Story Builder', description: 'Compose and manage narrative content and interactive forms', icon: 'auto_stories', category: 'Content', route: '/s101', status: 'built' },
  { id: 's100', name: 'Tool Builder', description: 'Create and configure custom tools for the system', icon: 'build', category: 'Development', route: '/s100', status: 'built' },
  { id: 's300', name: 'Workflow Builder', description: 'Design and orchestrate automated workflows', icon: 'account_tree', category: 'Automation', route: '/s300', status: 'built' },
  { id: 's310', name: 'Clipboard Orchestration', description: 'System clipboard buffer and overnight maintenance chain', icon: 'content_paste', category: 'Automation', route: '/s310', status: 'built' },
  { id: 's320', name: 'Knowledge Tools', description: 'AppFlowy workspace browser, document viewer, semantic search', icon: 'auto_stories', category: 'Knowledge', route: '/s320', status: 'built' },
  { id: 's330', name: 'Migration Dashboard', description: 'Data migration and consolidation dashboard', icon: 'compare_arrows', category: 'Data', route: '/s330', status: 'built' },
  { id: 's200', name: 'Health Dashboard', description: 'System health monitoring dashboard', icon: 'monitor_heart', category: 'Status', route: '/s200', status: 'stub' },
  { id: 's600', name: 'Learning Hub', description: 'Tutorials, guides, educational resources', icon: 'school', category: 'Learning', route: '/s600', status: 'built' },
]

function ServicesPanel() {
  const categories = Array.from(new Set(SERVICES.map(t => t.category)))
  return (
    <article className="container-fluid" style={{ margin: '12px', maxWidth: '960px' }}>
      <header>
        <hgroup>
          <h5>System Services</h5>
          <p style={{ margin: 0 }}>Non-S-page services — backend bridges, syncers, processors</p>
        </hgroup>
      </header>
      {categories.map(category => (
        <div key={category} style={{ marginBottom: '16px' }}>
          <h6 style={{ margin: '0 0 8px 0' }}>{category}</h6>
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))' }}>
            {SERVICES.filter(t => t.category === category).map(service => (
              <div key={service.id} className="outline" role="button" style={{ padding: '12px', textAlign: 'left', cursor: 'default', opacity: service.status === 'active' ? 1 : 0.6 }}>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                  <Icon name={service.icon as any} size={20} />
                  <div>
                    <strong>{service.name}</strong><br />
                    <small>{service.description}</small><br />
                    <kbd style={{ marginTop: '6px', display: 'inline-block' }}>{service.status === 'active' ? service.actionLabel : 'Coming soon'}</kbd>
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

function SPageToolsPanel() {
  const navigate = useNavigate()
  return (
    <article className="container-fluid" style={{ margin: '12px', maxWidth: '960px' }}>
      <header>
        <hgroup>
          <h5>System Tools</h5>
          <p style={{ margin: 0 }}>S-page tools that DO something — click to open</p>
        </hgroup>
      </header>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
        {S_PAGE_TOOLS.map(tool => (
          <div key={tool.id} className="outline" role="button" onClick={() => navigate(`/system?tab=tools&page=${tool.id}`)} style={{ padding: '16px', textAlign: 'left', cursor: 'pointer' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
              <Icon name={tool.icon as any} size={24} />
              <div>
                <strong>{tool.name}</strong><br />
                <small>{tool.description}</small><br />
                <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
                  <kbd>{tool.route}</kbd>
                  <kbd>{tool.status}</kbd>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <footer style={{ marginTop: '16px' }}>
        <small>Backend services managed in <a href="/server?tab=services" style={{ color: 'var(--pico-primary)' }}>/server → Services</a></small>
      </footer>
    </article>
  )
}

export { ServicesPanel, SPageToolsPanel }
export default function SystemToolsSurface() { return null }