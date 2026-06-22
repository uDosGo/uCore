/* ═══════════════════════════════════════════════════════════════════
   VaultSidebar — Vault/Binder file-picker sidebar
   Purely a vault sidebar: binder selector + file search + file list.
   No tasks, no publish, no extraneous binders.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react'
import { Icon } from './Icon'

// ─── Types ──────────────────────────────────────────────────────────
export interface VaultFile {
  id: number
  name: string
  type: string
  size: number
  updatedAt: string
  tags?: string[]
  binder?: string
}

export interface Binder {
  id: string
  name: string
  path: string
  icon?: string
  description?: string
  fileCount?: number
}

export interface SidebarNavItem {
  id: string
  icon: string
  label: string
  active?: boolean
  onClick: () => void
}

// ─── Allowed uDoS file types ────────────────────────────────────────
const UDOS_EXTENSIONS = new Set(['.md', '.json', '.yaml', '.yml', '.txt', '.csv'])

function isUdosFile(name: string): boolean {
  const ext = name.substring(name.lastIndexOf('.')).toLowerCase()
  return UDOS_EXTENSIONS.has(ext)
}

// ─── Binders (workspaces) — vault/binder only ──────────────────────
const BINDERS: Binder[] = [
  { id: 'uConnect',     name: 'uConnect',     path: '~/Code/uConnect',          icon: 'hub',         description: 'Unified Surface XD — main app suite', fileCount: 42 },
  { id: 'uCode1',       name: 'uCode1',       path: '~/Code/uCode1',            icon: 'code',        description: 'Code1 surface', fileCount: 15 },
  { id: 'uCode2',       name: 'uCode2',       path: '~/Code/uCode2',            icon: 'code',        description: 'Code2 surface', fileCount: 12 },
  { id: 'uServer',      name: 'uServer',      path: '~/Code/uServer',           icon: 'dns',         description: 'uServer backend services', fileCount: 22 },
  { id: 'uSystem',      name: 'uSystem',      path: '~/Code/uSystem',           icon: 'settings',    description: 'System configuration & tools', fileCount: 35 },
  { id: 'uPlace',       name: 'uPlace',       path: '~/Code/uPlace',            icon: 'location_on', description: 'Location-based services', fileCount: 11 },
  { id: 'SonicScrewdriver', name: 'SonicScrewdriver', path: '~/Code/SonicScrewdriver', icon: 'build', description: 'Build & tooling utilities', fileCount: 6 },
  { id: 'Groovebox',    name: 'Groovebox',     path: '~/Code/Groovebox',        icon: 'music_note',  description: 'Audio / music tools', fileCount: 4 },
]

const DEFAULT_BINDER = BINDERS[0]

// ─── Mock files per binder (uDoS types only) ────────────────────────
const BINDER_FILES: Record<string, VaultFile[]> = {
  uConnect: [
    { id: 1, name: 'Project Notes.md', type: 'md', size: 2048, updatedAt: new Date(Date.now() - 3600000).toISOString(), tags: ['notes', 'project'], binder: 'uConnect' },
    { id: 2, name: 'config.yaml', type: 'yaml', size: 1024, updatedAt: new Date(Date.now() - 86400000 * 5).toISOString(), tags: ['config'], binder: 'uConnect' },
    { id: 3, name: 'README.md', type: 'md', size: 4096, updatedAt: new Date(Date.now() - 86400000 * 7).toISOString(), tags: ['docs'], binder: 'uConnect' },
    { id: 4, name: 'package.json', type: 'json', size: 512, updatedAt: new Date(Date.now() - 86400000).toISOString(), tags: ['config', 'npm'], binder: 'uConnect' },
    { id: 5, name: 'tsconfig.json', type: 'json', size: 768, updatedAt: new Date(Date.now() - 86400000 * 3).toISOString(), tags: ['config', 'typescript'], binder: 'uConnect' },
    { id: 6, name: 'CHANGELOG.md', type: 'md', size: 6144, updatedAt: new Date(Date.now() - 86400000 * 2).toISOString(), tags: ['docs', 'changelog'], binder: 'uConnect' },
    { id: 7, name: 'tasks.md', type: 'md', size: 1536, updatedAt: new Date(Date.now() - 1800000).toISOString(), tags: ['tasks', 'todo'], binder: 'uConnect' },
  ],
  uCode1: [
    { id: 101, name: 'main.py', type: 'txt', size: 2048, updatedAt: new Date(Date.now() - 86400000 * 4).toISOString(), tags: ['python'], binder: 'uCode1' },
    { id: 102, name: 'README.md', type: 'md', size: 1024, updatedAt: new Date(Date.now() - 86400000).toISOString(), tags: ['docs'], binder: 'uCode1' },
  ],
  uServer: [
    { id: 401, name: 'README.md', type: 'md', size: 2048, updatedAt: new Date(Date.now() - 86400000 * 14).toISOString(), tags: ['docs'], binder: 'uServer' },
    { id: 402, name: 'requirements.txt', type: 'txt', size: 256, updatedAt: new Date(Date.now() - 86400000 * 7).toISOString(), tags: ['config', 'python'], binder: 'uServer' },
    { id: 403, name: 'config.yaml', type: 'yaml', size: 1024, updatedAt: new Date(Date.now() - 86400000 * 3).toISOString(), tags: ['config'], binder: 'uServer' },
  ],
}

// ─── Helpers ────────────────────────────────────────────────────────
const formatRelativeTime = (dateString: string): string => {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
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

const getFileIcon = (name: string): string => {
  const ext = name.substring(name.lastIndexOf('.')).toLowerCase()
  const map: Record<string, string> = {
    '.md': 'description',
    '.json': 'data_object',
    '.yaml': 'code',
    '.yml': 'code',
    '.txt': 'article',
    '.csv': 'table_rows',
  }
  return map[ext] || 'insert_drive_file'
}

// ─── Props ──────────────────────────────────────────────────────────
interface VaultSidebarProps {
  open: boolean
  /** Optional: if provided, shows a "New" button that calls this */
  onNewFile?: (binderId: string) => void
  /** Optional: called when a file is selected */
  onFileSelect?: (file: VaultFile) => void
  /** Optional: compact mode for embedded use (e.g. chat panel) */
  compact?: boolean
  /** Optional: show server/filepicker mode tabs (used by Server surface) */
  showModeTabs?: boolean
  /** Optional: selected sidebar mode */
  sidebarMode?: 'server' | 'filepicker'
  /** Optional: mode switch callback */
  onSidebarModeChange?: (mode: 'server' | 'filepicker') => void
  /** Optional: server navigation items shown when mode=server */
  serverNavItems?: SidebarNavItem[]
  /** Optional: externally supplied binders/workspaces */
  binders?: Binder[]
  /** Optional: externally supplied files for the active binder */
  files?: VaultFile[]
  /** Optional: externally supplied loading state for files */
  loadingFiles?: boolean
  /** Optional: externally controlled active binder */
  activeBinderId?: string
  /** Optional: binder change callback for externally controlled mode */
  onBinderChange?: (binderId: string) => void
  /** Optional: custom search placeholder */
  searchPlaceholder?: string
  /** Optional: custom empty-state hint */
  emptyHint?: string
}

// ─── Component ──────────────────────────────────────────────────────
const VaultSidebar: React.FC<VaultSidebarProps> = ({
  open,
  onNewFile,
  onFileSelect,
  compact = false,
  showModeTabs = false,
  sidebarMode = 'filepicker',
  onSidebarModeChange,
  serverNavItems = [],
  binders,
  files: externalFiles,
  loadingFiles,
  activeBinderId,
  onBinderChange,
  searchPlaceholder,
  emptyHint,
}) => {
  const availableBinders = binders && binders.length > 0 ? binders : BINDERS
  const [activeBinder, setActiveBinder] = useState<Binder>(DEFAULT_BINDER)
  const [binderDropdownOpen, setBinderDropdownOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [files, setFiles] = useState<VaultFile[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const binderRef = useRef<HTMLDivElement>(null)
  const isServerMode = showModeTabs && sidebarMode === 'server'
  const modeOrder: Array<'server' | 'filepicker'> = ['server', 'filepicker']

  useEffect(() => {
    const nextActive = availableBinders.find(b => b.id === activeBinderId) || availableBinders[0] || DEFAULT_BINDER
    if (nextActive && nextActive.id !== activeBinder.id) {
      setActiveBinder(nextActive)
    }
  }, [activeBinder.id, activeBinderId, availableBinders])

  // Load files for active binder
  const loadFiles = useCallback(async (binder: Binder) => {
    setIsLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 200))
      const wsFiles = BINDER_FILES[binder.id] || []
      setFiles(wsFiles.filter(f => isUdosFile(f.name)))
    } catch {
      setFiles([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (externalFiles) return
    loadFiles(activeBinder)
  }, [activeBinder, externalFiles, loadFiles])

  // Close binder dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (binderRef.current && !binderRef.current.contains(e.target as Node)) {
        setBinderDropdownOpen(false)
      }
    }
    if (binderDropdownOpen) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [binderDropdownOpen])

  const sourceFiles = externalFiles || files

  const filteredFiles = useMemo(() => {
    if (!searchQuery) return files
    const q = searchQuery.toLowerCase()
    return sourceFiles.filter(f =>
      f.name.toLowerCase().includes(q) ||
      (f.tags && f.tags.some(t => t.toLowerCase().includes(q)))
    )
  }, [searchQuery, sourceFiles])

  const handleModeKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!showModeTabs || !onSidebarModeChange) return
    const currentIdx = modeOrder.indexOf(sidebarMode)
    if (currentIdx === -1) return

    if (e.key === 'ArrowRight') {
      e.preventDefault()
      onSidebarModeChange(modeOrder[(currentIdx + 1) % modeOrder.length])
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      onSidebarModeChange(modeOrder[(currentIdx - 1 + modeOrder.length) % modeOrder.length])
    } else if (e.key === 'Home') {
      e.preventDefault()
      onSidebarModeChange(modeOrder[0])
    } else if (e.key === 'End') {
      e.preventDefault()
      onSidebarModeChange(modeOrder[modeOrder.length - 1])
    }
  }

  return (
    <div className="vault-sidebar-wrapper">
      {/* Sidebar panel — slides open/closed */}
      <div className={`vault-sidebar ${open ? 'vault-sidebar--open' : 'vault-sidebar--closed'} ${compact ? 'vault-sidebar--compact' : ''}`}>
        <div className="vault-sidebar-inner">
          {showModeTabs && (
            <div className="vault-sidebar-mode-switch" role="tablist" aria-label="Sidebar mode" onKeyDown={handleModeKeyDown}>
              <button
                className={`vault-sidebar-mode-btn ${sidebarMode === 'server' ? 'active' : ''}`}
                onClick={() => onSidebarModeChange?.('server')}
                role="tab"
                aria-selected={sidebarMode === 'server'}
                aria-controls="vault-sidebar-panel-server"
                id="vault-sidebar-tab-server"
                tabIndex={sidebarMode === 'server' ? 0 : -1}
              >
                <Icon name="dns" size={13} />
                <span>Dashbaord</span>
              </button>
              <button
                className={`vault-sidebar-mode-btn ${sidebarMode === 'filepicker' ? 'active' : ''}`}
                onClick={() => onSidebarModeChange?.('filepicker')}
                role="tab"
                aria-selected={sidebarMode === 'filepicker'}
                aria-controls="vault-sidebar-panel-filepicker"
                id="vault-sidebar-tab-filepicker"
                tabIndex={sidebarMode === 'filepicker' ? 0 : -1}
              >
                <Icon name="folder" size={13} />
                <span>Filepicker</span>
              </button>
            </div>
          )}

          {isServerMode ? (
            <div
              className="vault-sidebar-content vault-sidebar-content--server"
              role="tabpanel"
              id="vault-sidebar-panel-server"
              aria-labelledby="vault-sidebar-tab-server"
            >
              <div className="vault-sidebar-server-list">
                {serverNavItems.length === 0 ? (
                  <div className="vault-sidebar-empty">
                    <Icon name="dns" size={20} />
                    <span>No server tabs available</span>
                  </div>
                ) : (
                  serverNavItems.map(item => (
                    <button
                      key={item.id}
                      className={`vault-sidebar-server-item ${item.active ? 'active' : ''}`}
                      onClick={item.onClick}
                      title={item.label}
                    >
                      <Icon name={item.icon} size={14} />
                      <span>{item.label}</span>
                    </button>
                  ))
                )}
              </div>
            </div>
          ) : (
            <>
              {/* Binder selector */}
              <div
                className="vault-sidebar-binder-selector"
                ref={binderRef}
                role="tabpanel"
                id="vault-sidebar-panel-filepicker"
                aria-labelledby="vault-sidebar-tab-filepicker"
              >
                <button
                  className="vault-sidebar-binder-btn"
                  onClick={() => setBinderDropdownOpen(prev => !prev)}
                >
                  <Icon name={activeBinder.icon || 'folder'} size={14} />
                  <span className="vault-sidebar-binder-label">{activeBinder.name}</span>
                  <Icon name={binderDropdownOpen ? 'expand_less' : 'expand_more'} size={12} />
                </button>
                {binderDropdownOpen && (
                  <div className="vault-sidebar-binder-dropdown">
                    <div className="vault-sidebar-binder-list">
                      {availableBinders.map(b => {
                        const isActive = b.id === activeBinder.id
                        return (
                          <button
                            key={b.id}
                            className={`vault-sidebar-binder-item ${isActive ? 'active' : ''}`}
                            onClick={() => {
                              setActiveBinder(b)
                              onBinderChange?.(b.id)
                              setBinderDropdownOpen(false)
                              setSearchQuery('')
                            }}
                          >
                            <Icon name={b.icon || 'folder'} size={14} />
                            <div className="vault-sidebar-binder-item-info">
                              <span className="vault-sidebar-binder-item-name">{b.name}</span>
                              {b.fileCount !== undefined && (
                                <span className="vault-sidebar-binder-item-count">{b.fileCount} files</span>
                              )}
                            </div>
                            {isActive && <Icon name="check" size={12} />}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Scrollable content area — search + file list */}
              <div className="vault-sidebar-content">
                {/* Search */}
                <input
                  id="vault-sidebar-search-input"
                  type="search"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder={searchPlaceholder || 'Filter files'}
                  className="vault-sidebar-search-input"
                />

                {/* File list */}
                <div className="vault-sidebar-file-list">
                  {(loadingFiles ?? isLoading) ? (
                    <div className="vault-sidebar-loading">
                      <Icon name="sync" size={14} className="vault-sidebar-spin" />
                      <span>Loading...</span>
                    </div>
                  ) : filteredFiles.length === 0 ? (
                    <div className="vault-sidebar-empty">
                      <Icon name={searchQuery ? 'search_off' : 'folder_open'} size={20} />
                      <span>{searchQuery ? 'No files found' : 'No files in this binder'}</span>
                      {!searchQuery && (
                        <span className="vault-sidebar-empty-hint">{emptyHint || 'Create a new document to get started'}</span>
                      )}
                    </div>
                  ) : (
                    filteredFiles.map(file => (
                      <div
                        key={file.id}
                        className="vault-sidebar-file-item"
                        onClick={() => onFileSelect?.(file)}
                        title={file.name}
                      >
                        <Icon name={getFileIcon(file.name)} size={14} className="vault-sidebar-file-icon" />
                        <div className="vault-sidebar-file-info">
                          <span className="vault-sidebar-file-name">{file.name}</span>
                          <span className="vault-sidebar-file-meta">{formatRelativeTime(file.updatedAt)}</span>
                        </div>
                        {file.tags && file.tags.length > 0 && (
                          <span className="vault-sidebar-file-tag">{file.tags[0]}</span>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* New file button */}
              {onNewFile && (
                <div className="vault-sidebar-footer">
                  <button className="vault-sidebar-new-btn" onClick={() => onNewFile(activeBinder.id)}>
                    <Icon name="add" size={14} />
                    <span>New Document</span>
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

    </div>
  )
}

export default VaultSidebar
