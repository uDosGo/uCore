/* ═══════════════════════════════════════════════════════════════════
   TabsModule — Separated tab management for Sidebar/Topbar
   Provides unified tab system with Dev Tags support
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo, useCallback } from 'react'
import { Icon } from '../Icon'

// ─── Types ──────────────────────────────────────────────────────────
export type TabSource = 'user' | 'shared' | 'global' | 'code' | 'public'

export interface TabItem {
  id: string
  label: string
  icon?: string
  source?: TabSource
  tags?: string[]
  status?: 'active' | 'inactive' | 'deprecated' | 'placeholder'
  devTag?: string
  count?: number
}

export interface TabGroup {
  id: string
  label: string
  icon?: string
  tabs: TabItem[]
  defaultTab?: string
}

export interface TabsModuleProps {
  groups: TabGroup[]
  activeGroupId?: string
  activeTabId?: string
  onGroupChange?: (groupId: string) => void
  onTabChange?: (tabId: string) => void
  showDevTags?: boolean
  compact?: boolean
}

// ─── Dev Tags System ────────────────────────────────────────────────
export const DEV_TAGS = {
  WORKING: '✅',
  PLACEHOLDER: '⚪',
  DEPRECATED: '⛔',
  DUPLICATE: '🔁',
  LEGACY: '📜',
  EXPERIMENTAL: '🧪',
  BROKEN: '💥',
} as const

export type DevTagType = keyof typeof DEV_TAGS

// ─── Component ──────────────────────────────────────────────────────
export const TabsModule: React.FC<TabsModuleProps> = ({
  groups,
  activeGroupId,
  activeTabId,
  onGroupChange,
  onTabChange,
  showDevTags = true,
  compact = false,
}) => {
  const [selectedGroup, setSelectedGroup] = useState(activeGroupId || groups[0]?.id)
  const [selectedTab, setSelectedTab] = useState(activeTabId || groups[0]?.defaultTab)

  const activeGroup = useMemo(() => {
    return groups.find(g => g.id === selectedGroup) || groups[0]
  }, [groups, selectedGroup])

  const handleGroupSelect = useCallback((groupId: string) => {
    setSelectedGroup(groupId)
    onGroupChange?.(groupId)
  }, [onGroupChange])

  const handleTabSelect = useCallback((tabId: string) => {
    setSelectedTab(tabId)
    onTabChange?.(tabId)
  }, [onTabChange])

  const getDevTagIcon = (tag?: string) => {
    if (!tag || !showDevTags) return null
    return DEV_TAGS[tag as DevTagType] || null
  }

  return (
    <div className={`tabs-module ${compact ? 'tabs-module--compact' : ''}`}>
      {/* Group Tabs */}
      <div className="tabs-module-groups" role="tablist">
        {groups.map(group => (
          <button
            key={group.id}
            className={`tabs-module-group-btn ${selectedGroup === group.id ? 'active' : ''}`}
            onClick={() => handleGroupSelect(group.id)}
            role="tab"
            aria-selected={selectedGroup === group.id}
          >
            {group.icon && <Icon name={group.icon} size={16} />}
            <span>{group.label}</span>
            {group.tabs.length > 0 && (
              <span className="tabs-module-count">{group.tabs.length}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Items */}
      <div className="tabs-module-items">
        {activeGroup?.tabs.map(tab => (
          <button
            key={tab.id}
            className={`tabs-module-tab-btn ${selectedTab === tab.id ? 'active' : ''}`}
            onClick={() => handleTabSelect(tab.id)}
          >
            {tab.icon && <Icon name={tab.icon} size={14} />}
            <span className="tabs-module-tab-label">{tab.label}</span>
            {showDevTags && tab.devTag && (
              <span className="tabs-module-devtag" title={tab.devTag}>
                {getDevTagIcon(tab.devTag)}
              </span>
            )}
            {tab.count !== undefined && (
              <span className="tabs-module-tab-count">{tab.count}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── Sidebar Tabs Hook ────────────────────────────────────────────────
export const useSidebarTabs = (initialSource: TabSource = 'user') => {
  const [source, setSource] = useState<TabSource>(initialSource)
  const [activeBinder, setActiveBinder] = useState<string>('all')

  const sidebarGroups: TabGroup[] = [
    {
      id: 'workspace',
      label: 'Workspace',
      icon: 'folder',
      tabs: [
        { id: 'user', label: 'User Vault', icon: 'person', source: 'user', devTag: 'WORKING' },
        { id: 'shared', label: 'Shared Vault', icon: 'group', source: 'shared', devTag: 'WORKING' },
        { id: 'global', label: 'Global Vault', icon: 'public', source: 'global', devTag: 'WORKING' },
        { id: 'code', label: 'Code Repos', icon: 'code', source: 'code', devTag: 'WORKING' },
        { id: 'public', label: 'Public Sites', icon: 'web', source: 'public', devTag: 'EXPERIMENTAL' },
      ],
    },
    {
      id: 'binder',
      label: 'Binder / Mission',
      icon: 'collections_bookmark',
      tabs: [
        { id: 'all', label: 'All Binders', devTag: 'WORKING' },
        { id: 'active', label: 'Active Projects', devTag: 'WORKING' },
        { id: 'tasks', label: 'Tasks/Missions', devTag: 'WORKING' },
        { id: 'inbox', label: 'Inbox', devTag: 'WORKING' },
        { id: 'archive', label: 'Archive', devTag: 'WORKING' },
      ],
    },
    {
      id: 'search',
      label: 'Search / Tags',
      icon: 'search',
      tabs: [
        { id: 'search', label: 'Search', devTag: 'WORKING' },
        { id: 'tags', label: 'Tags', devTag: 'WORKING' },
      ],
    },
  ]

  return {
    source,
    setSource,
    activeBinder,
    setActiveBinder,
    sidebarGroups,
  }
}