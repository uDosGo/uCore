<template>
  <div class="filepicker-sidebar">
    <!-- Header -->
    <div class="filepicker-sidebar__header">
      <h3 class="filepicker-sidebar__title">Files</h3>
      <div class="filepicker-sidebar__header-actions">
        <UButton
          size="sm"
          variant="secondary"
          icon="sync"
          :disabled="isMirroring"
          @click="mirrorUserVault"
          title="Mirror User Vault to local AppFlowy"
        >
          {{ isMirroring ? 'Mirroring...' : 'Mirror User' }}
        </UButton>
        <UButton size="sm" icon="mdi:plus" @click="handleNewFile" title="New file">
          New
        </UButton>
      </div>
    </div>

    <div v-if="mirrorMessage" class="filepicker-sidebar__mirror-message">{{ mirrorMessage }}</div>

    <!-- Search Section -->
    <UInput
      v-model="searchQuery"
      placeholder="Search files..."
      icon="mdi:magnify"
      class="filepicker-sidebar__search"
    />

    <!-- Filters Section -->
    <div class="filepicker-sidebar__filters">
      <WorkspaceFilter ref="workspaceFilterRef" @source-change="onSourceChange" />
      <BinderMissionFilter ref="binderFilterRef" @binder-change="onBinderChange" />
    </div>

    <!-- Index Status Banner -->
    <div v-if="indexStatus === 'not-built'" class="filepicker-sidebar__banner">
      <span>Index not built</span>
      <UButton size="sm" @click="buildIndex">Build Index</UButton>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="filepicker-sidebar__loading">
      <USpinner :size="20" />
      <span>Loading files...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="filepicker-sidebar__error">
      <UIcon name="mdi:alert-circle-outline" />
      <span>{{ error }}</span>
      <UButton size="sm" @click="fetchFiles">Retry</UButton>
    </div>

    <!-- Files List Section -->
    <div v-else class="filepicker-sidebar__list">
      <div
        v-for="file in filteredFiles"
        :key="file.path"
        class="filepicker-sidebar__item"
        :class="{ 'filepicker-sidebar__item--readonly': file.is_readonly }"
        @click="emit('fileSelect', file)"
        @dblclick="handleDoubleClick(file)"
      >
        <UIcon :name="getFileIcon(file.extension)" class="filepicker-sidebar__item-icon" />
        <div class="filepicker-sidebar__item-info">
          <span class="filepicker-sidebar__item-name">{{ file.filename }}</span>
          <span class="filepicker-sidebar__item-path">{{ file.path }}</span>
        </div>
        <div class="filepicker-sidebar__item-meta">
          <UBadge
            v-if="file.vault_layer"
            :type="getLayerBadgeType(file.vault_layer)"
          >
            {{ file.vault_layer }}
          </UBadge>
          <span v-if="file.is_readonly" class="filepicker-sidebar__readonly-icon" title="Read-only">
            <UIcon name="mdi:lock-outline" />
          </span>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredFiles.length === 0 && !loading" class="filepicker-sidebar__empty">
        <UIcon name="mdi:file-document-outline" />
        <span v-if="searchQuery">No files matching "{{ searchQuery }}"</span>
        <span v-else>No files found in this vault layer</span>
        <UButton size="sm" variant="ghost" @click="handleNewFile">
          Create a new file
        </UButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component FilepickerSidebar
 * @description Unified filepicker sidebar — vault layer → binder/mission → search.
 * Wired to the uCore unified library index API with vault plate integration.
 * @category molecules
 * @props {boolean} open - Sidebar visibility
 * @props {boolean} compact - Compact mode
 * @emits {FileEntry} fileSelect - File selected
 * @emits {string} newFile - New file requested
 * @usage <FilepickerSidebar :open="true" @file-select="handleFileSelect" />
 */
import { ref, computed, onMounted, watch } from 'vue'
import UInput from '../atoms/UInput.vue'
import UIcon from '../atoms/UIcon.vue'
import UBadge from '../atoms/UBadge.vue'
import UButton from '../atoms/UButton.vue'
import USpinner from '../atoms/USpinner.vue'
import WorkspaceFilter from './WorkspaceFilter.vue'
import BinderMissionFilter from './BinderMissionFilter.vue'
import { ucoreApi } from '../../api/client'
import type { FileEntry } from '../../types/filepicker'

interface Props {
  open?: boolean
  compact?: boolean
}

withDefaults(defineProps<Props>(), {
  open: true,
  compact: false,
})

const emit = defineEmits<{
  fileSelect: [file: FileEntry]
  newFile: [binderId: string]
}>()

// ─── Refs ───────────────────────────────────────────────────────────
const workspaceFilterRef = ref<InstanceType<typeof WorkspaceFilter>>()
const binderFilterRef = ref<InstanceType<typeof BinderMissionFilter>>()

const searchQuery = ref('')
const selectedSource = ref<string>('')
const selectedBinder = ref<string>('')
const files = ref<FileEntry[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const indexStatus = ref<'ok' | 'not-built' | 'unknown'>('unknown')
const isMirroring = ref(false)
const mirrorMessage = ref('')

// ─── Fetch files from the unified library index ────────────────────
async function fetchFiles() {
  loading.value = true
  error.value = null
  try {
    const query = searchQuery.value.trim() || '*'
    const res = await ucoreApi.library.search(
      query,
      selectedSource.value || undefined,
    )
    if (res.ok && res.data) {
      const results = (res.data as any).results || []
      files.value = results

      // Extract unique binders from results to populate binder filter
      const binderSet = new Set<string>()
      results.forEach((f: FileEntry) => {
        if (f.binder) binderSet.add(f.binder)
        if (f.mission) binderSet.add(f.mission)
      })
      const binderList = Array.from(binderSet).map(id => ({ id, name: id }))
      if (binderList.length > 0 && binderFilterRef.value) {
        binderFilterRef.value.setBinders([
          { id: 'active', name: 'Active' },
          { id: 'docs', name: 'Documentation' },
          { id: 'archive', name: 'Archive' },
          ...binderList,
        ])
      }
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch files'
    files.value = []
  } finally {
    loading.value = false
  }
}

// ─── Build index ────────────────────────────────────────────────────
async function buildIndex() {
  loading.value = true
  try {
    const res = await ucoreApi.library.build()
    if (res.ok) {
      indexStatus.value = 'ok'
      await fetchFiles()
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to build index'
  } finally {
    loading.value = false
  }
}

// ─── Check index status on mount ────────────────────────────────────
async function checkIndex() {
  try {
    const res = await ucoreApi.library.stats()
    if (res.ok) {
      const total = (res.data as any)?.total_entries || 0
      indexStatus.value = total > 0 ? 'ok' : 'not-built'
    }
  } catch {
    indexStatus.value = 'unknown'
  }
}

// ─── Debounced search ───────────────────────────────────────────────
let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchFiles(), 300)
})

function onSourceChange(source: string) {
  selectedSource.value = source
  if (source === 'user') {
    void mirrorUserVault()
  }
  fetchFiles()
}

function onBinderChange(binder: string) {
  selectedBinder.value = binder
  // Re-filter locally or re-fetch
  fetchFiles()
}

function handleNewFile() {
  emit('newFile', selectedBinder.value || 'active')
}

function handleDoubleClick(file: FileEntry) {
  // Could open in editor or navigate
  emit('fileSelect', file)
}

async function mirrorUserVault() {
  isMirroring.value = true
  mirrorMessage.value = ''
  try {
    const res = await ucoreApi.vault.sync('User Vault')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    mirrorMessage.value = 'User Vault mirrored to local AppFlowy.'
  } catch (e: any) {
    mirrorMessage.value = `Mirror failed: ${e?.message || e}`
  } finally {
    isMirroring.value = false
  }
}

onMounted(async () => {
  await checkIndex()
  if (indexStatus.value === 'ok') {
    await fetchFiles()
  }
})

// ─── Computed ───────────────────────────────────────────────────────
const filteredFiles = computed(() => {
  let result = files.value

  // Apply binder filter locally if set
  if (selectedBinder.value) {
    result = result.filter(f =>
      f.binder === selectedBinder.value || f.mission === selectedBinder.value,
    )
  }

  return result
})

// ─── Icon mapping ───────────────────────────────────────────────────
function getFileIcon(ext: string): string {
  const iconMap: Record<string, string> = {
    md: 'mdi:language-markdown',
    ts: 'mdi:language-typescript',
    tsx: 'mdi:language-typescript',
    vue: 'mdi:vuejs',
    json: 'mdi:code-json',
    yaml: 'mdi:file-code',
    yml: 'mdi:file-code',
    py: 'mdi:language-python',
    js: 'mdi:language-javascript',
    jsx: 'mdi:language-javascript',
    css: 'mdi:language-css3',
    html: 'mdi:language-html5',
    txt: 'mdi:text',
    csv: 'mdi:file-delimited',
    toml: 'mdi:file-cog',
    env: 'mdi:key-variant',
    sh: 'mdi:console',
    svg: 'mdi:svg',
    png: 'mdi:file-image',
    jpg: 'mdi:file-image',
    jpeg: 'mdi:file-image',
    gif: 'mdi:file-image',
    pdf: 'mdi:file-pdf',
    doc: 'mdi:file-word',
    docx: 'mdi:file-word',
    xls: 'mdi:file-excel',
    xlsx: 'mdi:file-excel',
  }
  return iconMap[ext] || 'mdi:file-document-outline'
}

function getLayerBadgeType(layer: string): 'info' | 'success' | 'warning' | 'error' {
  const map: Record<string, 'info' | 'success' | 'warning' | 'error'> = {
    User: 'info',
    Shared: 'success',
    Global: 'warning',
    Public: 'warning',
    Code: 'error',
  }
  return map[layer] || 'info'
}
</script>

<style scoped>
.filepicker-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--usx-spacing-md);
  gap: var(--usx-spacing-sm);
}

.filepicker-sidebar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: var(--usx-spacing-xs);
  border-bottom: 1px solid rgba(88, 166, 255, 0.1);
}

.filepicker-sidebar__header-actions {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.filepicker-sidebar__title {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: 600;
  color: var(--pico-color);
}

.filepicker-sidebar__search {
  flex-shrink: 0;
}

.filepicker-sidebar__mirror-message {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: color-mix(in srgb, var(--usx-color-info) 10%, transparent);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
}

.filepicker-sidebar__filters {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) 0;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(88, 166, 255, 0.1);
}

.filepicker-sidebar__banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: rgba(210, 153, 34, 0.1);
  border-radius: var(--usx-border-radius-sm);
  font-size: var(--usx-font-size-sm);
  color: #d29922;
  flex-shrink: 0;
}

.filepicker-sidebar__list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.filepicker-sidebar__item {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-border-radius-sm);
  cursor: pointer;
  transition: background 0.1s ease;
  min-height: var(--usx-input-height-sm);
}

.filepicker-sidebar__item:hover {
  background: rgba(88, 166, 255, 0.08);
}

.filepicker-sidebar__item--readonly {
  opacity: 0.7;
}

.filepicker-sidebar__item-icon {
  flex-shrink: 0;
  color: var(--usx-color-on-surface-muted);
  font-size: 1.5em;
}

.filepicker-sidebar__item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.filepicker-sidebar__item-name {
  font-size: var(--usx-font-size-sm);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filepicker-sidebar__item-path {
  font-size: var(--usx-font-size-xs);
  color: var(--pico-muted-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filepicker-sidebar__item-meta {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-shrink: 0;
}

.filepicker-sidebar__readonly-icon {
  color: var(--pico-muted-color);
  display: flex;
  align-items: center;
}

.filepicker-sidebar__loading,
.filepicker-sidebar__error,
.filepicker-sidebar__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-lg);
  color: var(--pico-muted-color);
  font-size: var(--usx-font-size-sm);
  text-align: center;
}

.filepicker-sidebar__error {
  color: #f85149;
}
</style>
