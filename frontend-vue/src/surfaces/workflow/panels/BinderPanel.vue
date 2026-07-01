<template>
  <div class="wf-section">
    <h4 class="wf-section-title">Binder Cross-Reference</h4>
    <p class="wf-section-desc">Mission/task/binder cross-reference from knowledge index</p>

    <!-- Launchpad — drop files to compile into a Binder -->
    <div class="wf-launchpad">
      <div
        class="wf-launchpad-drop"
        :class="{ 'wf-launchpad-drop--active': isDragging }"
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
      >
        <UIcon name="publish" />
        <span class="wf-launchpad-prompt">Start here — drop files to compile into a Binder</span>
        <span class="wf-launchpad-hint">Drag .md, .yaml, .json, .py files or folders</span>
        <div v-if="launchpadFiles.length > 0" class="wf-launchpad-files">
          <div v-for="(file, idx) in launchpadFiles" :key="idx" class="wf-launchpad-file">
            <UIcon :name="fileIcon(file.name)" />
            <span>{{ file.name }}</span>
            <span class="wf-launchpad-file-size">{{ formatSize(file.size) }}</span>
            <button class="wf-launchpad-remove" @click="removeFile(idx)" title="Remove">
              <UIcon name="close" />
            </button>
          </div>
        </div>
        <button
          v-if="launchpadFiles.length > 0"
          class="usx-button usx-btn--primary"
          @click="compileBinder"
        >
          <UIcon name="build" /> Compile Binder
        </button>
      </div>
    </div>

    <div v-if="wf.loading" class="wf-loading">
      <UIcon name="sync" /> Loading binder data...
    </div>

    <!-- Summary stats -->
    <div v-if="wf.missionTaskBinderRows.length > 0" class="wf-stats">
      <div class="wf-stat">
        <span class="wf-stat-value" style="color:#d29922">{{ missionCount }}</span>
        <span class="wf-stat-label">Missions</span>
      </div>
      <div class="wf-stat">
        <span class="wf-stat-value" style="color:#58a6ff">{{ binderCount }}</span>
        <span class="wf-stat-label">Binders</span>
      </div>
      <div class="wf-stat">
        <span class="wf-stat-value">{{ wf.missionTaskBinderRows.length }}</span>
        <span class="wf-stat-label">Total Rows</span>
      </div>
    </div>

    <!-- Filters -->
    <div class="wf-binder-filters" v-if="wf.missionTaskBinderRows.length > 0">
      <input
        v-model="filterMission"
        class="wf-filter-input"
        placeholder="Filter by mission..."
        type="text"
      />
      <input
        v-model="filterBinder"
        class="wf-filter-input"
        placeholder="Filter by binder..."
        type="text"
      />
    </div>

    <!-- Binder table -->
    <div v-if="filteredRows.length > 0" class="wf-binder-table-wrap">
      <table class="wf-binder-table">
        <thead>
          <tr>
            <th>Mission</th>
            <th>Task</th>
            <th>Binder</th>
            <th>Title</th>
            <th>Workspace</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in paginatedRows" :key="idx">
            <td>
              <UBadge type="warning" size="sm">{{ row.mission }}</UBadge>
            </td>
            <td class="wf-monospace">{{ row.task }}</td>
            <td>
              <UBadge type="info" size="sm">{{ row.binder }}</UBadge>
            </td>
            <td class="wf-title-cell">{{ row.title }}</td>
            <td class="wf-monospace wf-muted">{{ row.workspace_id }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="wf-pagination">
      <button class="usx-button" :disabled="page <= 0" @click="page--">Prev</button>
      <span class="wf-page-indicator">Page {{ page + 1 }} / {{ totalPages }}</span>
      <button class="usx-button" :disabled="page >= totalPages - 1" @click="page++">Next</button>
    </div>

    <div v-if="wf.missionTaskBinderRows.length === 0 && !wf.loading" class="wf-empty">
      No mission/task/binder bindings found. Import knowledge documents with mission, task, and binder metadata.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import { useWorkflowStore } from '../../../stores/workflow'
import type { MissionTaskBinderRow } from '../../../stores/workflow'

const wf = useWorkflowStore()
const PAGE_SIZE = 25

const filterMission = ref('')
const filterBinder = ref('')
const page = ref(0)

const filteredRows = computed<MissionTaskBinderRow[]>(() => {
  let rows = wf.missionTaskBinderRows
  if (filterMission.value) {
    const m = filterMission.value.toLowerCase()
    rows = rows.filter(r => r.mission.toLowerCase().includes(m))
  }
  if (filterBinder.value) {
    const b = filterBinder.value.toLowerCase()
    rows = rows.filter(r => r.binder.toLowerCase().includes(b))
  }
  return rows
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / PAGE_SIZE)))

const paginatedRows = computed(() => {
  const start = page.value * PAGE_SIZE
  return filteredRows.value.slice(start, start + PAGE_SIZE)
})

const missionCount = computed(() => new Set(wf.missionTaskBinderRows.map(r => r.mission)).size)
const binderCount = computed(() => new Set(wf.missionTaskBinderRows.map(r => r.binder)).size)

// Reset page when filters change
watch([filterMission, filterBinder], () => { page.value = 0 })

// ─── Launchpad drop-zone ────────────────────────────────────────────
interface LaunchpadFile {
  name: string
  size: number
  type: string
}

const isDragging = ref(false)
const launchpadFiles = ref<LaunchpadFile[]>([])

function onDragOver() {
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  if (!e.dataTransfer?.files) return
  const newFiles: LaunchpadFile[] = []
  for (let i = 0; i < e.dataTransfer.files.length; i++) {
    const f = e.dataTransfer.files[i]
    newFiles.push({ name: f.name, size: f.size, type: f.type || '' })
  }
  launchpadFiles.value = [...launchpadFiles.value, ...newFiles]
}

function removeFile(idx: number) {
  launchpadFiles.value.splice(idx, 1)
}

function fileIcon(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || ''
  const map: Record<string, string> = {
    md: 'mdi:language-markdown', yaml: 'mdi:file-code', yml: 'mdi:file-code',
    json: 'mdi:code-json', py: 'mdi:language-python', ts: 'mdi:language-typescript',
    vue: 'mdi:vuejs', js: 'mdi:language-javascript', css: 'mdi:language-css3',
    html: 'mdi:language-html5', toml: 'mdi:file-cog', sh: 'mdi:console',
  }
  return map[ext] || 'mdi:file-document-outline'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function compileBinder(): Promise<void> {
  // Send files to backend /api/knowledge/import endpoint
  console.log('Compiling binder with', launchpadFiles.value.length, 'files')
  wf.loading = true
  try {
    const API = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'
    for (const f of launchpadFiles.value) {
      await fetch(`${API}/api/knowledge/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          binder: 'launchpad',
          mission: 'launchpad',
          files: [f.name],
        }),
        signal: AbortSignal.timeout(15000),
      })
    }
    launchpadFiles.value = []
    await wf.fetchMissionTaskBinder()
  } catch (e: any) {
    console.warn('Binder compile failed:', e)
  } finally {
    wf.loading = false
  }
}
</script>

<style scoped>
.wf-launchpad {
  flex-shrink: 0;
}

.wf-launchpad-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xl) var(--usx-spacing-lg);
  border: 2px dashed rgba(88, 166, 255, 0.2);
  border-radius: var(--usx-border-radius-lg);
  background: rgba(88, 166, 255, 0.02);
  transition: all 0.15s ease;
  min-height: 120px;
  cursor: pointer;
}

.wf-launchpad-drop--active,
.wf-launchpad-drop:hover {
  border-color: rgba(88, 166, 255, 0.5);
  background: rgba(88, 166, 255, 0.06);
}

.wf-launchpad-prompt {
  font-size: var(--usx-font-size-sm);
  font-weight: 600;
  color: var(--pico-color);
}

.wf-launchpad-hint {
  font-size: var(--usx-font-size-xs);
  color: var(--pico-muted-color);
}

.wf-launchpad-files {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  width: 100%;
  max-width: 420px;
}

.wf-launchpad-file {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  background: var(--pico-card-background-color);
  border-radius: var(--usx-border-radius-sm);
  font-size: var(--usx-font-size-sm);
}

.wf-launchpad-file-size {
  font-size: var(--usx-font-size-xs);
  color: var(--pico-muted-color);
  margin-left: auto;
}

.wf-launchpad-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-xs);
  border: none;
  background: transparent;
  color: var(--pico-muted-color);
  cursor: pointer;
  border-radius: var(--usx-border-radius-sm);
  transition: all 0.1s ease;
}

.wf-launchpad-remove:hover {
  color: #f85149;
  background: rgba(248, 81, 73, 0.1);
}

.wf-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  color: var(--pico-muted-color);
  font-size: var(--usx-font-size-sm);
}

.wf-stats {
  display: flex;
  gap: var(--usx-spacing-md);
  flex-wrap: wrap;
}

.wf-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-md);
  background: var(--pico-card-background-color);
  border-radius: var(--usx-border-radius-lg);
  min-width: 90px;
  flex: 1;
}

.wf-stat-value {
  font-size: var(--usx-font-size-xl);
  font-weight: 700;
  line-height: var(--usx-line-height-tight);
}

.wf-stat-label {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
}

.wf-binder-filters {
  display: flex;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.wf-filter-input {
  flex: 1;
  min-width: 180px;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: 1px solid var(--pico-border-color);
  border-radius: var(--usx-border-radius-md);
  background: var(--pico-card-background-color);
  color: var(--pico-color);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family);
}

.wf-filter-input::placeholder {
  color: var(--pico-muted-color);
}

.wf-binder-table-wrap {
  overflow-x: auto;
  border-radius: var(--usx-border-radius-lg);
  border: 1px solid var(--pico-border-color);
}

.wf-binder-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--usx-font-size-sm);
}

.wf-binder-table th {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  text-align: left;
  font-weight: 600;
  color: var(--pico-muted-color);
  background: var(--pico-card-background-color);
  border-bottom: 1px solid var(--pico-border-color);
  white-space: nowrap;
}

.wf-binder-table td {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: 1px solid var(--pico-muted-background-color);
  vertical-align: top;
}

.wf-binder-table tbody tr:hover {
  background: var(--pico-muted-background-color);
}

.wf-monospace {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
}

.wf-muted {
  color: var(--pico-muted-color);
}

.wf-title-cell {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wf-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-md);
}

.wf-page-indicator {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
}

.wf-empty {
  padding: var(--usx-spacing-xl);
  text-align: center;
  color: var(--pico-muted-color);
  font-size: var(--usx-font-size-sm);
}
</style>