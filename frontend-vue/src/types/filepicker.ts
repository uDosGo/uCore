/**
 * @module types/filepicker
 * @description Type definitions for the filepicker sidebar and vault integration.
 */

export interface FileEntry {
  id: string
  path: string
  filename: string
  source: string
  vault_layer: string
  binder: string | null
  mission: string | null
  tags: string[]
  extension: string
  size: number
  modified_at: string
  preview: string | null
  is_readonly?: boolean
  is_shared?: boolean
  is_published?: boolean
}

export interface VaultLayer {
  id: string
  label: string
  icon: string
  description: string
  path: string
  fileCount?: number
}

export interface LibrarySearchResult {
  query: string
  source: string | null
  count: number
  results: FileEntry[]
}

export interface LibraryStats {
  status: string
  index_path: string
  total_entries: number
  by_source: Record<string, number>
  last_build: string | null
}
