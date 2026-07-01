/* ═══════════════════════════════════════════════════════════════════
   FilepickerSidebar — Unified uihub Filepicker sidebar
   Three-filter-box system: Workspace → Binder/Mission → Search/Tags
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo, useCallback } from 'react'
import { Icon } from './Icon'
import { WorkspaceFilter } from './WorkspaceFilter'
import { BinderMissionFilter } from './BinderMissionFilter'
import { FileSource, FileEntry } from '../types/filepicker'

// ─── Props ──────────────────────────────────────────────────────────
interface FilepickerSidebarProps {
  open: boolean
  onFileSelect?: (file: FileEntry) => void
  onNewFile?: (binderId: string) => void
  compact?: boolean
}

// ─── Sidebar Navigation Item Type ─────────────────────────────────────
export interface SidebarNavItem {
  id: string
  icon: string
  label: string
  active?: boolean
  onClick: () => void
}

// ─── Mock data for now (will connect to vault_file_discovery API) ─────
const MOCK_FILES: FileEntry[] = [
  {
    path: '~/Vault/notes.md',
    filename: 'notes.md',
    source: 'user',
    vault_layer: 'User',
    binder: 'active',
    mission: null,
    tags: ['notes'],
    type: 'file',
    extension: 'md',
    size: 2048,
    modified_at: new Date(Date.now() - 3600000),
    created_at: new Date(Date.now() - 86400000),
    is_readonly: false,
    is_shared: false,
    is_published: false,
    frontmatter: {},
    preview: 'Personal notes and thoughts...',
  },
  {
    path: '~/Vault/guide.md',
    filename: 'guide.md',
    source: 'shared',
    vault_layer: 'Shared',
    binder: 'docs',
    mission: null,
    tags: ['documentation'],
    type: 'file',
    extension: 'md',
    size: 4096,
    modified_at: new Date(Date.now() - 86400000 * 5),
    created_at: new Date(Date.now() - 86400000 * 10),
    is_readonly: false,
    is_shared: true,
    is_published: false,
    frontmatter: {},
    preview: 'Shared documentation guide...',
  },
  {
    path: '~/Code/README.md',
    filename: 'README.md',
    source: 'code',
    vault_layer: 'Code',
    binder: 'docs',
    mission: null,
    tags: ['documentation'],
    type: 'file',
    extension: 'md',
    size: 8192,
    modified_at: new Date(Date.now() - 86400000 * 2),
    created_at: new Date(Date.now() - 86400000 * 7),
    is_readonly: false,
    is_shared: false,
    is_published: false,
    frontmatter: {},
    preview: 'uCore project documentation...',
  },
  {
    path: '~/Vault/system.md',
    filename: 'system.md',
    source: 'global',
    vault_layer: 'Global',
    binder: 'system',
    mission: null,
    tags: ['system', 'config'],
    type: 'file',
    extension: 'md',
    size: 3072,
    modified_at: new Date(Date.now() - 86400000),
    created_at: new Date(Date.now() - 86400000 * 3),
    is_readonly: false,
    is_shared: false,
    is_published: false,
    frontmatter: {},
    preview: 'System configuration and settings...',
  },
  {
    path: '~/Public/deploy.yaml',
    filename: 'deploy.yaml',
    source: 'public',
    vault_layer: 'Public',
    binder: 'ops',
    mission: null,
    tags: ['deployment', 'config'],
    type: 'file',
    extension: 'yaml',
    size: 1024,
    modified_at: new Date(Date.now() - 86400000),
    created_at: new Date(Date.now() - 86400000 * 5),
    is_readonly: false,
    is_shared: false,
    is_published: true,
    frontmatter: {},
    preview: 'Deployment configuration...',
  },
]

// ─── Helper ──────────────────────────────────────────────────────────
const formatRelativeTime = (date: Date): string => {
  const diff = Date.now() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

// ─── Component ──────────────────────────────────────────────────────
export const FilepickerSidebar: React.FC<FilepickerSidebarProps> = ({
  open,
  onFileSelect,
  onNewFile,
  compact = false,
}) => {
  const [workspace, setWorkspace] = useState<FileSource | 'all'>('all')
  const [workspaceToggles, setWorkspaceToggles] = useState<Record<string, boolean>>({
    user: true,
    shared: true,
    global: true,
    code: true,
    public: true,
  })
  const [binder, setBinder] = useState<'all' | 'uCore' | 'Knowledge' | 'System'>('all')
  const [mission, setMission] = useState<'all' | 'Alpha' | 'Beta' | 'Archived'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchTags, setSearchTags] = useState<string[]>([])

  // Apply filters
  const filteredFiles = useMemo(() => {
    let results = [...MOCK_FILES]

    // Workspace filter
    if (workspace !== 'all') {
      results = results.filter(f => f.source === workspace)
    } else {
      const enabled = Object.entries(workspaceToggles)
        .filter(([, v]) => v)
        .map(([k]) => k)
      results = results.filter(f => enabled.includes(f.source))
    }

    // Binder filter
    if (binder === 'uCore') {
      results = results.filter(f => f.binder === 'uCore')
    } else if (binder === 'Knowledge') {
      results = results.filter(f => f.binder === 'Knowledge')
    } else if (binder === 'System') {
      results = results.filter(f => f.binder === 'System')
    }

    // Mission filter
    if (mission === 'Alpha') {
      results = results.filter(f => f.mission === 'Alpha')
    } else if (mission === 'Beta') {
      results = results.filter(f => f.mission === 'Beta')
    } else if (mission === 'Archived') {
      results = results.filter(f => f.mission === 'Archived')
    }

    // Search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      results = results.filter(f =>
        f.filename.toLowerCase().includes(q) ||
        f.preview.toLowerCase().includes(q) ||
        f.tags.some(t => t.toLowerCase().includes(q))
      )
    }

    // Tag filter
    if (searchTags.length > 0) {
      results = results.filter(f => searchTags.some(t => f.tags.includes(t)))
    }

    return results
  }, [workspace, workspaceToggles, binder, mission, searchQuery, searchTags])

  const handleWorkspaceChange = useCallback((ws: FileSource | 'all') => {
    setWorkspace(ws)
  }, [])

  const handleToggleChange = useCallback((toggles: Record<string, boolean>) => {
    setWorkspaceToggles(toggles)
  }, [])

  const handleBinderChange = useCallback((b: typeof binder) => {
    setBinder(b)
  }, [])

  const handleMissionChange = useCallback((m: typeof mission) => {
    setMission(m)
  }, [])

  return (
    <div className={`filepicker-sidebar ${open ? 'filepicker-sidebar--open' : 'filepicker-sidebar--closed'} ${compact ? 'filepicker-sidebar--compact' : ''}`}>
      <div className="filepicker-sidebar-inner">
        {/* Box 1: Workspace Filter */}
        <WorkspaceFilter
          selected={workspace}
          onWorkspaceChange={handleWorkspaceChange}
          onToggleChange={handleToggleChange}
          compact={compact}
        />

        {/* Box 2: Binder/Mission Filter */}
        <BinderMissionFilter
          selected={binder}
          onChange={handleBinderChange}
          chips={searchTags}
          onChipRemove={(tag) => setSearchTags(searchTags.filter(t => t !== tag))}
          onAddChip={() => {}}
          compact={compact}
        />

        {/* Box 3: Search/Tags */}
        <div className="filepicker-search-box">
          <div className="filepicker-search-input-wrapper">
            <Icon name="search" size={14} />
            <input
              type="text"
              placeholder="Search across files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="filepicker-search-input"
            />
            {searchQuery && (
              <button
                className="filepicker-clear-btn"
                onClick={() => setSearchQuery('')}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>
          <div className="filepicker-tag-pills">
            {searchTags.map(tag => (
              <span key={tag} className="filepicker-tag-pill">
                #{tag}
              </span>
            ))}
          </div>
        </div>

        {/* File List */}
        <div className="filepicker-file-list">
          {filteredFiles.length === 0 ? (
            <div className="filepicker-empty">
              <Icon name="folder_open" size={20} />
              <span>No files found</span>
            </div>
          ) : (
            filteredFiles.map(file => (
              <div
                key={file.path}
                className="filepicker-file-item"
                onClick={() => onFileSelect?.(file)}
              >
                <Icon name="description" size={14} />
                <div className="filepicker-file-info">
                  <span className="filepicker-file-name">{file.filename}</span>
                  <span className="filepicker-file-meta">
                    {file.vault_layer} • {file.binder || 'no binder'} • {formatRelativeTime(file.modified_at)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Status Bar */}
        <div className="filepicker-status-bar">
          Showing {filteredFiles.length} results
          {(workspace !== 'all' || binder !== 'all' || searchQuery || searchTags.length > 0) && (
            <span> ({[workspace !== 'all', binder !== 'all', searchQuery, searchTags.length > 0].filter(Boolean).length} filters active)</span>
          )}
        </div>
      </div>
    </div>
  )
}

export default FilepickerSidebar