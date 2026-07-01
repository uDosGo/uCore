/* ═══════════════════════════════════════════════════════════════════
   BinderMissionFilter — Binder/Mission dropdown selector with checkboxes
   Part of the three-filter-box system: Workspace → Binder/Mission → Search/Tags
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useCallback } from 'react'
import { Icon } from './Icon'

// ─── Types ──────────────────────────────────────────────────────────
interface BinderMissionFilterProps {
  selected: 'all' | 'uCore' | 'Knowledge' | 'System' | 'Alpha' | 'Beta' | 'Archived'
  onChange: (binder: 'all' | 'uCore' | 'Knowledge' | 'System' | 'Alpha' | 'Beta' | 'Archived') => void
  chips?: string[]
  onChipRemove?: (chip: string) => void
  onAddChip?: () => void
  compact?: boolean
}

// ─── Binder Options ─────────────────────────────────────────────────
const BINDER_OPTIONS: Array<{
  id: 'all' | 'uCore' | 'Knowledge' | 'System'
  name: string
  icon: string
}> = [
  { id: 'all', name: 'All', icon: 'list' },
  { id: 'uCore', name: 'uCore', icon: 'folder' },
  { id: 'Knowledge', name: 'Knowledge', icon: 'school' },
  { id: 'System', name: 'System', icon: 'settings' },
]

// ─── Mission Options ─────────────────────────────────────────────────
const MISSION_OPTIONS: Array<{
  id: 'all' | 'Alpha' | 'Beta' | 'Archived'
  name: string
  icon: string
}> = [
  { id: 'all', name: 'All', icon: 'list' },
  { id: 'Alpha', name: 'Alpha', icon: 'rocket_launch' },
  { id: 'Beta', name: 'Beta', icon: 'flag' },
  { id: 'Archived', name: 'Archived', icon: 'archive' },
]

// ─── Component ──────────────────────────────────────────────────────
export const BinderMissionFilter: React.FC<BinderMissionFilterProps> = ({
  selected,
  onChange,
  chips = [],
  onChipRemove,
  onAddChip,
  compact = false,
}) => {
  const [binder, setBinder] = useState<'all' | 'uCore' | 'Knowledge' | 'System'>('all')
  const [mission, setMission] = useState<'all' | 'Alpha' | 'Beta' | 'Archived'>('all')

  const handleBinderChange = useCallback((b: typeof binder) => {
    setBinder(b)
    onChange(b)
  }, [binder, onChange])

  const handleMissionChange = useCallback((m: typeof mission) => {
    setMission(m)
    onChange(m)
  }, [mission, onChange])

  return (
    <div className={`binder-mission-filter ${compact ? 'binder-mission-filter--compact' : ''}`}>
      <div className="binder-mission-filter-header">
        <span className="binder-mission-filter-title">📂 Binder</span>
        <select
          className="binder-mission-filter-select"
          value={binder}
          onChange={(e) => handleBinderChange(e.target.value as typeof binder)}
        >
          {BINDER_OPTIONS.map(opt => (
            <option key={opt.id} value={opt.id}>
              {opt.name}
            </option>
          ))}
        </select>
      </div>

      <div className="binder-mission-filter-header">
        <span className="binder-mission-filter-title">🎯 Mission</span>
        <select
          className="binder-mission-filter-select"
          value={mission}
          onChange={(e) => handleMissionChange(e.target.value as typeof mission)}
        >
          {MISSION_OPTIONS.map(opt => (
            <option key={opt.id} value={opt.id}>
              {opt.name}
            </option>
          ))}
        </select>
      </div>

      <div className="binder-mission-filter-chips">
        {BINDER_OPTIONS.slice(1).map(opt => (
          <button
            key={opt.id}
            className={`binder-mission-chip ${binder === opt.id ? 'active' : ''}`}
            onClick={() => handleBinderChange(opt.id)}
          >
            <span className="binder-mission-chip-check">○</span>
            <span>{opt.name}</span>
          </button>
        ))}

        {MISSION_OPTIONS.slice(1).map(opt => (
          <button
            key={opt.id}
            className={`binder-mission-chip ${mission === opt.id ? 'active' : ''}`}
            onClick={() => handleMissionChange(opt.id)}
          >
            <span className="binder-mission-chip-check">○</span>
            <span>{opt.name}</span>
          </button>
        ))}

        {chips.map(chip => (
          <button
            key={chip}
            className="binder-mission-chip custom"
            onClick={() => onChipRemove?.(chip)}
            title={`Remove ${chip}`}
          >
            <span>{chip}</span>
            <span className="chip-remove">✕</span>
          </button>
        ))}

        <button
          className="binder-mission-chip add"
          onClick={onAddChip}
          title="Add custom binder"
        >
          <span>+</span>
        </button>
      </div>
    </div>
  )
}

export default BinderMissionFilter