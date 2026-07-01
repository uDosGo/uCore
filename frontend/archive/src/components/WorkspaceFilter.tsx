/* ═══════════════════════════════════════════════════════════════════
   WorkspaceFilter — Simple workspace dropdown selector
   Part of the three-filter-box system: Workspace → Binder/Mission → Search/Tags
   ═══════════════════════════════════════════════════════════════════ */
import React, { useCallback } from 'react'
import { FileSource } from '../types/filepicker'

// ─── Types ──────────────────────────────────────────────────────────
interface WorkspaceFilterProps {
  selected: FileSource | 'all'
  onWorkspaceChange: (workspace: FileSource | 'all') => void
  compact?: boolean
}

// ─── Workspace Options ───────────────────────────────────────────────
const WORKSPACE_OPTIONS: Array<{
  id: FileSource
  name: string
  icon: string
  label: string
}> = [
  { id: 'user', name: 'User Vault', icon: 'person', label: '👤 User Vault' },
  { id: 'shared', name: 'Shared Vault', icon: 'group', label: '🤝 Shared Vault' },
  { id: 'global', name: 'Global Vault', icon: 'public', label: '🌍 Global Vault' },
  { id: 'code', name: 'Code Repos', icon: 'code', label: '💻 Code Repos' },
  { id: 'public', name: 'Public Sites', icon: 'web', label: '📢 Public Sites' },
]

// ─── Component ──────────────────────────────────────────────────────
export const WorkspaceFilter: React.FC<WorkspaceFilterProps> = ({
  selected,
  onWorkspaceChange,
  compact = false,
}) => {
  const handleSelect = useCallback((workspace: FileSource | 'all') => {
    onWorkspaceChange(workspace)
  }, [onWorkspaceChange])

  return (
    <div className={`workspace-filter ${compact ? 'workspace-filter--compact' : ''}`}>
      <div className="workspace-filter-header">
        <span className="workspace-filter-title">📍 Workspace</span>
        <select
          className="workspace-filter-select"
          value={selected}
          onChange={(e) => handleSelect(e.target.value as FileSource | 'all')}
        >
          <option value="all">🌐 All Workspaces</option>
          {WORKSPACE_OPTIONS.map(opt => (
            <option key={opt.id} value={opt.id}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
