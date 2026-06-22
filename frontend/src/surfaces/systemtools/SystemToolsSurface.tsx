/* ═══════════════════════════════════════════════════════════════════
   SystemToolsSurface — System Pages Browser & Administration
   ═══════════════════════════════════════════════════════════════════
   First-class surface for system pages (S100-S899) — tools, pages,
   modules, settings, and administrative functions.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GlobalToolbar } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import { SettingsPanel } from '../system/SettingsPanel'
import '../../styles/hub/index.css'

type SystemToolsTab = 'pages' | 'tools' | 'settings'

interface SystemPageEntry {
  code: string
  name: string
  description: string
  icon: string
  category: string
  route: string
}

// ─── Tools Registry ──────────────────────────────────────────────
interface Tool {
  id: string
  name: string
  description: string
  icon: string
  category: string
  route?: string
  action?: () => void
}

const TOOLS: Tool[] = [
  {
    id: 'tool-builder',
    name: 'Tool Builder',
    description: 'Create custom tools and utilities',
    icon: 'build',
    category: 'Development',
    route: '/s100',
  },
  {
    id: 'workflow-executor',
    name: 'Workflow Executor',
    description: 'Run and monitor automated workflows',
    icon: 'play_arrow',
    category: 'Automation',
    route: '/s300',
  },
  {
    id: 'clipboard-sync',
    name: 'Clipboard Sync',
    description: 'Sync clipboard across devices',
    icon: 'content_paste',
    category: 'Integration',
    route: '/s310',
  },
  {
    id: 'data-importer',
    name: 'Data Importer',
    description: 'Import data from external sources',
    icon: 'upload',
    category: 'Data',
  },
  {
    id: 'batch-processor',
    name: 'Batch Processor',
    description: 'Process multiple items in parallel',
    icon: 'settings_suggest',
    category: 'Processing',
  },
  {
    id: 'scheduler',
    name: 'Task Scheduler',
    description: 'Schedule recurring tasks and jobs',
    icon: 'schedule',
    category: 'Automation',
  },
]

function ToolCard({ tool, onClick }: { tool: Tool; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '16px',
        border: '1px solid var(--pico-form-element-border-color, #30363d)',
        borderRadius: '6px',
        cursor: 'pointer',
        transition: 'all 200ms ease',
        background: 'var(--pico-card-background-color, #0d1117)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = '#58a6ff'
        e.currentTarget.style.background = 'var(--pico-card-background-color, #0d1117)'
        e.currentTarget.style.boxShadow = '0 0 12px rgba(88, 166, 255, 0.2)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--pico-form-element-border-color, #30363d)'
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '6px',
            background: '#58a6ff20',
            color: '#58a6ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <Icon name={tool.icon} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600' }}>{tool.name}</h4>
            <span style={{ fontSize: '10px', color: 'var(--pico-muted-color, #8b949e)', background: 'var(--pico-form-element-background-color, #0d1117)', padding: '2px 6px', borderRadius: '3px' }}>
              {tool.category}
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '12px', color: 'var(--pico-muted-color, #8b949e)', lineHeight: '1.4' }}>
            {tool.description}
          </p>
        </div>
      </div>
    </div>
  )
}

function ToolsPanel() {
  const navigate = useNavigate()

  const handleToolClick = (tool: Tool) => {
    if (tool.route) {
      navigate(tool.route)
    } else if (tool.action) {
      tool.action()
    }
  }

  // Group tools by category
  const categories = Array.from(new Set(TOOLS.map(t => t.category)))

  return (
    <div style={{ padding: '24px', maxWidth: '900px' }}>
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>Available Tools</h2>
        <p style={{ margin: 0, fontSize: '14px', color: 'var(--pico-muted-color, #8b949e)' }}>
          Access and manage system tools and utilities
        </p>
      </div>

      {categories.map((category) => (
        <div key={category} style={{ marginBottom: '32px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600', color: 'var(--pico-muted-color, #8b949e)', textTransform: 'uppercase' }}>
            {category}
          </h3>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
              gap: '12px',
            }}
          >
            {TOOLS.filter(t => t.category === category).map((tool) => (
              <ToolCard key={tool.id} tool={tool} onClick={() => handleToolClick(tool)} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── System Pages Registry ──────────────────────────────────────────
const SYSTEM_PAGES: SystemPageEntry[] = [
  // Tools
  {
    code: 'S100',
    name: 'Tool Builder',
    description: 'Create and configure custom tools for the system',
    icon: 'build',
    category: 'tools',
    route: '/s100',
  },
  {
    code: 'S101',
    name: 'Story Builder',
    description: 'Compose and manage narrative content',
    icon: 'article',
    category: 'tools',
    route: '/s101',
  },
  {
    code: 'S300',
    name: 'Workflow Builder',
    description: 'Design and orchestrate workflows',
    icon: 'schema',
    category: 'tools',
    route: '/s300',
  },
  {
    code: 'S310',
    name: 'Clipboard Orchestration',
    description: 'Manage clipboard operations and data flow',
    icon: 'content_paste',
    category: 'tools',
    route: '/s310',
  },
  {
    code: 'S320',
    name: 'Knowledge Tools',
    description: 'Knowledge base management and search',
    icon: 'school',
    category: 'tools',
    route: '/s320',
  },
]

function SystemPageCard({ page, onClick }: { page: SystemPageEntry; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '16px',
        border: '1px solid var(--pico-form-element-border-color, #30363d)',
        borderRadius: '6px',
        cursor: 'pointer',
        transition: 'all 200ms ease',
        background: 'var(--pico-card-background-color, #0d1117)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = '#58a6ff'
        e.currentTarget.style.background = 'var(--pico-card-background-color, #0d1117)'
        e.currentTarget.style.boxShadow = '0 0 12px rgba(88, 166, 255, 0.2)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--pico-form-element-border-color, #30363d)'
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '6px',
            background: '#58a6ff20',
            color: '#58a6ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <Icon name={page.icon} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600' }}>{page.name}</h4>
            <code style={{ fontSize: '11px', color: 'var(--pico-muted-color, #8b949e)' }}>{page.code}</code>
          </div>
          <p style={{ margin: 0, fontSize: '12px', color: 'var(--pico-muted-color, #8b949e)', lineHeight: '1.4' }}>
            {page.description}
          </p>
        </div>
      </div>
    </div>
  )
}

function SystemPagesPanel() {
  const navigate = useNavigate()

  return (
    <div style={{ padding: '24px', maxWidth: '900px' }}>
      <div style={{ marginTop: '0', paddingTop: '0' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600' }}>System Pages Reference</h3>
        <div style={{ fontSize: '12px', color: 'var(--pico-muted-color, #8b949e)', lineHeight: '1.6' }}>
          <p>
            <strong>S100-S199:</strong> Tool builders and asset creation
          </p>
          <p>
            <strong>S200-S299:</strong> Content management
          </p>
          <p>
            <strong>S300-S399:</strong> Workflow and orchestration
          </p>
          <p>
            <strong>S400-S499:</strong> Integration and modules
          </p>
          <p>
            <strong>S500-S599:</strong> Security and configuration
          </p>
          <p>
            <strong>S600-S699:</strong> Learning and documentation
          </p>
          <p>
            <strong>S700-S799:</strong> Advanced features
          </p>
          <p>
            <strong>S800-S899:</strong> System status and diagnostics
          </p>
        </div>
      </div>
    </div>
  )
}

interface SystemToolsSurfaceProps {
  embedded?: boolean
}

export { ToolsPanel, SystemPagesPanel }

export default function SystemToolsSurface({ embedded = false }: SystemToolsSurfaceProps) {
  const [activeTab, setActiveTab] = useState<SystemToolsTab>('pages')

  const tabs = [
    { id: 'pages', icon: 'dashboard', label: 'Pages' },
    { id: 'tools', icon: 'build', label: 'Tools' },
    { id: 'settings', icon: 'settings', label: 'Settings' },
  ]

  if (embedded) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--pico-background-color, #010409)' }}>
        <div style={{ display: 'flex', gap: '8px', padding: '12px 16px', borderBottom: '1px solid var(--pico-form-element-border-color, #30363d)' }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as SystemToolsTab)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 10px',
                borderRadius: '6px',
                border: '1px solid var(--pico-form-element-border-color, #30363d)',
                background: activeTab === tab.id ? '#58a6ff20' : 'transparent',
                color: activeTab === tab.id ? '#58a6ff' : 'var(--pico-muted-color, #8b949e)',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              <Icon name={tab.icon} size={14} />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <div style={{ flex: 1, overflow: 'auto', background: 'var(--pico-background-color, #010409)' }}>
          {activeTab === 'pages' && <SystemPagesPanel />}
          {activeTab === 'tools' && <ToolsPanel />}
          {activeTab === 'settings' && <SettingsPanel />}
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--pico-background-color, #010409)' }}>
      <GlobalToolbar
        tabs={tabs.map((tab) => ({
          ...tab,
          active: activeTab === tab.id,
          onClick: () => setActiveTab(tab.id as SystemToolsTab),
        }))}
        rightExtra={<span style={{ fontSize: '12px', color: 'var(--pico-muted-color, #8b949e)' }}>System Tools · S100-S899</span>}
      />

      <div style={{ flex: 1, overflow: 'auto', background: 'var(--pico-background-color, #010409)' }}>
        {activeTab === 'pages' && <SystemPagesPanel />}
        {activeTab === 'tools' && (
          <ToolsPanel />
        )}
        {activeTab === 'settings' && <SettingsPanel />}
      </div>
    </div>
  )
}
