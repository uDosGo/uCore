/* ═══════════════════════════════════════════════════════════════════
   Filepicker Types — TypeScript interfaces for uihub Filepicker
   ═══════════════════════════════════════════════════════════════════ */

// ─── Source Types ───────────────────────────────────────────────────
export type FileSource = 'user' | 'shared' | 'global' | 'code' | 'public'

// ─── File Entry Schema (unified with VaultFile) ─────────────────────
export interface FileEntry {
  id?: number
  path: string
  filename: string
  name?: string
  source: FileSource
  vault_layer?: 'User' | 'Shared' | 'Global' | 'Code' | 'Public'
  binder: string | null
  mission?: string | null
  tags: string[]
  type: 'file' | 'folder' | 'symlink'
  extension?: string
  size: number
  modified_at: Date | string
  created_at?: Date
  is_readonly?: boolean
  is_shared?: boolean
  is_published?: boolean
  frontmatter?: Record<string, unknown>
  preview?: string
  updatedAt?: string
}

// ─── Filepicker State ────────────────────────────────────────────────
export interface FilepickerState {
  // Box 1: Workspace
  workspace: {
    selected: FileSource | 'all'
    toggles: {
      user: boolean
      shared: boolean
      global: boolean
      code: boolean
      public: boolean
    }
  }

  // Box 2: Binder/Mission
  binder_mission: {
    selected: 'all' | 'active' | 'tasks' | 'inbox' | 'archive' | string
    chips: string[]
    custom_binder: string | null
  }

  // Box 3: Search/Tags
  search: {
    query: string
    tags: string[]
    mode: 'search' | 'tag' | 'combined'
  }

  // Results
  results: FileEntry[]
  totalCount: number
  filteredCount: number
}

// ─── Filter Options ─────────────────────────────────────────────────
export interface FilterOptions {
  workspace?: FileSource | 'all'
  binder?: string | null
  mission?: string | null
  tags?: string[]
  searchQuery?: string
}

// ─── Workspace Switcher State ───────────────────────────────────────
export interface WorkspaceSwitcherState {
  top_level: Array<{
    id: string
    name: string
    path: string
    type: 'vault' | 'repo' | 'site'
  }>
  sub_workspaces: Record<string, Array<{
    id: string
    name: string
    path: string
  }>>
  transport_zones: string[]
  publishing_flow: string[]
}

// ─── Dev Tags ───────────────────────────────────────────────────────
export type DevTag = 'WORKING' | 'PLACEHOLDER' | 'DEPRECATED' | 'DUPLICATE' | 'LEGACY' | 'EXPERIMENTAL' | 'BROKEN'

export const DEV_TAG_ICONS: Record<DevTag, string> = {
  WORKING: '✅',
  PLACEHOLDER: '⚪',
  DEPRECATED: '⛔',
  DUPLICATE: '🔁',
  LEGACY: '📜',
  EXPERIMENTAL: '🧪',
  BROKEN: '💥',
}

// ─── File Assessment ───────────────────────────────────────────────
export interface FileAssessment {
  path: string
  dev_tag: DevTag
  confidence: number
  reasons: string[]
  line_matches: number[]
}