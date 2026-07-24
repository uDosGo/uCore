<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Repositories</h3>
      <UBadge type="info">{{ loading ? '...' : (repos.length || dev.repos.length) }} repos</UBadge>
    </div>
    <div class="repos-layout">
      <section class="repos-list-pane">
        <UInput v-model="filter" placeholder="Filter repos..." icon="search" class="developer-panel-search" />
        <div class="developer-card-list">
          <div v-for="repo in filteredRepos" :key="repo.name" class="developer-card" :class="{ 'developer-card--active': selectedRepo === repo.name }">
            <div class="developer-card-header">
              <UIcon name="folder" />
              <span class="developer-card-title">{{ repo.name }}</span>
              <UBadge :type="repo.status === 'clean' ? 'success' : 'warning'" size="sm">
                <template v-if="repo.status === 'clean'">
                  <UIcon name="check" :size="14" /> Clean
                </template>
                <template v-else>
                  <UIcon name="warning" :size="14" /> {{ repo.changes }} changes
                </template>
              </UBadge>
            </div>
            <div class="developer-card-meta">
              <span>⎇ {{ repo.branch }}</span>
              <span>{{ repo.path }}</span>
            </div>
            <div class="developer-card-remote">{{ repo.remote }}</div>
            <div class="developer-card-actions">
              <UButton variant="secondary" size="sm" @click="browseRepo(repo.name)">Browse</UButton>
              <UButton variant="ghost" size="sm" @click="openReviewTab">Review</UButton>
            </div>
          </div>
        </div>
      </section>

      <section class="repos-editor-pane">
        <div class="repos-editor-header">
          <div>
            <h4 class="repos-editor-title">{{ selectedRepo ? selectedRepo : 'Repo Browser' }}</h4>
            <p class="repos-editor-subtitle">{{ selectedRepo ? (selectedFilePath || 'Select a file from the list') : 'Choose a repo and click Browse to open files' }}</p>
          </div>
          <div class="repos-editor-actions">
            <UButton variant="ghost" size="sm" :disabled="!selectedRepo || filesLoading" @click="loadRepoFiles(selectedRepo)">
              Refresh Files
            </UButton>
            <UButton variant="secondary" size="sm" :disabled="!canSave || saving" @click="saveCurrentFile">
              {{ saving ? 'Saving...' : 'Save' }}
            </UButton>
          </div>
        </div>

        <div v-if="selectedRepo" class="repos-editor-content">
          <aside class="repo-files-panel">
            <UInput v-model="fileFilter" placeholder="Filter files..." icon="search" class="repo-files-search" />
            <div v-if="stagedFiles.length || unstagedFiles.length" class="repo-status-groups">
              <div v-if="stagedFiles.length" class="repo-status-group">
                <div class="repo-status-group-title">Staged ({{ stagedFiles.length }})</div>
                <button
                  v-for="file in stagedFiles.slice(0, 8)"
                  :key="`staged-${file.file}`"
                  class="repo-status-item"
                  @click="openFile(file.file)"
                >
                  <UIcon name="check_circle" :size="12" />
                  <span>{{ file.file }}</span>
                </button>
              </div>
              <div v-if="unstagedFiles.length" class="repo-status-group">
                <div class="repo-status-group-title">Unstaged ({{ unstagedFiles.length }})</div>
                <button
                  v-for="file in unstagedFiles.slice(0, 8)"
                  :key="`unstaged-${file.file}`"
                  class="repo-status-item"
                  @click="openFile(file.file)"
                >
                  <UIcon name="edit" :size="12" />
                  <span>{{ file.file }}</span>
                </button>
              </div>
            </div>
            <div class="repo-files-list">
              <button
                v-for="file in filteredFiles"
                :key="file.name"
                class="repo-file-item"
                :class="{ 'repo-file-item--active': selectedFilePath === file.name }"
                @click="openFile(file.name)"
              >
                <UIcon name="description" :size="14" />
                <span>{{ file.name }}</span>
              </button>
              <div v-if="filesLoading" class="repo-files-empty">Loading files...</div>
              <div v-else-if="filteredFiles.length === 0" class="repo-files-empty">No matching files.</div>
            </div>
          </aside>

          <div class="repo-editor-panel">
            <div v-if="selectedFilePath" class="repo-editor-wrap">
              <div class="repo-editor-toolbar">
                <UBadge size="sm" :type="fileGitStatus === 'added' ? 'info' : (fileGitStatus === 'deleted' ? 'danger' : 'warning')">
                  {{ fileGitStatusLabel }}
                </UBadge>
                <div class="repo-editor-toolbar-actions">
                  <UButton variant="ghost" size="sm" :disabled="!selectedFilePath || staging" @click="stageCurrentFile">
                    {{ staging ? 'Staging...' : 'Stage' }}
                  </UButton>
                  <UButton variant="ghost" size="sm" :disabled="!selectedFilePath || unstaging" @click="unstageCurrentFile">
                    {{ unstaging ? 'Unstaging...' : 'Unstage' }}
                  </UButton>
                </div>
              </div>
              <textarea v-model="fileContent" class="repo-editor" spellcheck="false" />
              <div class="repo-diff-panel">
                <div class="repo-diff-header">
                  <span>Diff Preview</span>
                  <UButton variant="ghost" size="sm" :disabled="!selectedFilePath || diffLoading" @click="refreshDiff">
                    {{ diffLoading ? 'Refreshing...' : 'Refresh Diff' }}
                  </UButton>
                </div>
                <pre class="repo-diff-content">{{ diffText || 'No local diff for this file.' }}</pre>
              </div>
              <div class="repo-commit-row">
                <input
                  v-model="commitMessage"
                  class="repo-commit-input"
                  type="text"
                  placeholder="Commit message"
                />
                <UButton variant="secondary" size="sm" :disabled="!selectedRepo || committing || !commitMessage.trim()" @click="commitRepo">
                  {{ committing ? 'Committing...' : 'Commit Repo' }}
                </UButton>
              </div>
              <div class="repo-editor-status">
                <span>{{ saveMessage || 'Ready' }}</span>
                <span v-if="isDirty" class="repo-editor-dirty">Unsaved changes</span>
              </div>
            </div>
            <div v-else class="repo-editor-empty">
              Select a file to preview and edit.
            </div>
          </div>
        </div>

        <div v-else class="repos-editor-empty">
          Browse a repository to open its file browser and editor pane.
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component ReposPanel
 * @description Repository browser panel — list, filter, browse repos.
 * @category surfaces/developer
 */
import { ref, computed, onMounted } from 'vue'
import UInput from '../../../skills/atoms/UInput.vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'
import { useDeveloperStore } from '../../../stores/developer'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'
const dev = useDeveloperStore()
const filter = ref('')
const fileFilter = ref('')
const loading = ref(true)
const filesLoading = ref(false)
const fileLoading = ref(false)
const saving = ref(false)
const selectedRepo = ref<string>('')
const selectedFilePath = ref<string>('')
const files = ref<Array<{ name: string; type: string; size: number }>>([])
const fileContent = ref('')
const originalFileContent = ref('')
const saveMessage = ref('')
const diffText = ref('')
const diffLoading = ref(false)
const staging = ref(false)
const unstaging = ref(false)
const committing = ref(false)
const commitMessage = ref('Update files')
const fileGitStatus = ref('modified')
const stagedFiles = ref<Array<{ file: string; status: string }>>([])
const unstagedFiles = ref<Array<{ file: string; status: string }>>([])

interface RepoData {
  id?: string
  name: string
  path: string
  branch: string
  status: string
  changes: number
  remote: string
  fileCount?: number
}

const repos = ref<RepoData[]>([])

async function fetchRepos() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/developer/repos`, {
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) {
      const data = await res.json()
      repos.value = data.repos || []
    }
  } catch {
    // Fallback to store samples
    repos.value = dev.repos.map(r => ({ name: r.name, path: r.path, branch: r.branch, status: r.status, changes: r.changes, remote: r.remote }))
  } finally {
    loading.value = false
  }
}

function browseRepo(name: string) {
  dev.browseRepo(name)
  selectedRepo.value = name
  selectedFilePath.value = ''
  fileContent.value = ''
  originalFileContent.value = ''
  saveMessage.value = ''
  diffText.value = ''
  fileGitStatus.value = 'modified'
  fileFilter.value = ''
  stagedFiles.value = []
  unstagedFiles.value = []
  void loadRepoFiles(name)
  void loadRepoStatus(name)
}

async function loadRepoFiles(repoName: string) {
  filesLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/developer/repos/${encodeURIComponent(repoName)}/files`, {
      signal: AbortSignal.timeout(6000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const payload = await res.json()
    files.value = Array.isArray(payload.files) ? payload.files : []
  } catch {
    files.value = []
  } finally {
    filesLoading.value = false
  }
}

async function loadRepoStatus(repoName: string) {
  try {
    const res = await fetch(
      `${API_BASE}/api/developer/repos/${encodeURIComponent(repoName)}/status`,
      { signal: AbortSignal.timeout(6000) },
    )
    if (res.ok) {
      const payload = await res.json()
      stagedFiles.value = Array.isArray(payload.staged) ? payload.staged : []
      unstagedFiles.value = Array.isArray(payload.unstaged) ? payload.unstaged : []
      return
    }

    const reviewRes = await fetch(
      `${API_BASE}/api/developer/repos/${encodeURIComponent(repoName)}/review`,
      { signal: AbortSignal.timeout(6000) },
    )
    if (!reviewRes.ok) throw new Error(`HTTP ${reviewRes.status}`)
    const reviewPayload = await reviewRes.json()
    const review = Array.isArray(reviewPayload.review) ? reviewPayload.review : []

    stagedFiles.value = []
    unstagedFiles.value = review.map((item: any) => ({
      file: String(item.file || ''),
      status: String(item.status || 'modified'),
    })).filter((item: { file: string }) => item.file.length > 0)
  } catch {
    stagedFiles.value = []
    unstagedFiles.value = []
  }
}

async function openFile(path: string) {
  if (!selectedRepo.value) return
  fileLoading.value = true
  saveMessage.value = ''
  try {
    const res = await fetch(
      `${API_BASE}/api/developer/repos/${encodeURIComponent(selectedRepo.value)}/file-preview?path=${encodeURIComponent(path)}`,
      { signal: AbortSignal.timeout(6000) },
    )
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const payload = await res.json()
    selectedFilePath.value = path
    fileContent.value = String(payload.content || '')
    originalFileContent.value = fileContent.value
    await loadDiff(path)
  } catch {
    saveMessage.value = 'Failed to open file'
  } finally {
    fileLoading.value = false
  }
}

async function loadDiff(path: string) {
  if (!selectedRepo.value) return
  diffLoading.value = true
  try {
    const res = await fetch(
      `${API_BASE}/api/developer/repos/${encodeURIComponent(selectedRepo.value)}/diff?path=${encodeURIComponent(path)}`,
      { signal: AbortSignal.timeout(6000) },
    )
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const payload = await res.json()
    diffText.value = payload.hasDiff ? String(payload.diff || '') : ''
    fileGitStatus.value = String(payload.status || 'modified')
  } catch {
    diffText.value = ''
  } finally {
    diffLoading.value = false
  }
}

async function saveCurrentFile() {
  if (!selectedRepo.value || !selectedFilePath.value || !isDirty.value) return
  saving.value = true
  saveMessage.value = ''
  try {
    const res = await fetch(
      `${API_BASE}/api/developer/repos/${encodeURIComponent(selectedRepo.value)}/file-preview?path=${encodeURIComponent(selectedFilePath.value)}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: fileContent.value }),
        signal: AbortSignal.timeout(8000),
      },
    )
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    originalFileContent.value = fileContent.value
    saveMessage.value = 'Saved'
    await loadDiff(selectedFilePath.value)
  } catch {
    saveMessage.value = 'Save failed'
  } finally {
    saving.value = false
  }
}

async function stageCurrentFile() {
  if (!selectedRepo.value || !selectedFilePath.value) return
  staging.value = true
  saveMessage.value = ''
  try {
    if (isDirty.value) {
      await saveCurrentFile()
    }
    const res = await fetch(
      `${API_BASE}/api/developer/repos/${encodeURIComponent(selectedRepo.value)}/stage?path=${encodeURIComponent(selectedFilePath.value)}`,
      { method: 'POST', signal: AbortSignal.timeout(6000) },
    )
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    saveMessage.value = 'Staged'
    await loadDiff(selectedFilePath.value)
    await fetchRepos()
    await loadRepoStatus(selectedRepo.value)
  } catch {
    saveMessage.value = 'Stage failed'
  } finally {
    staging.value = false
  }
}

async function unstageCurrentFile() {
  if (!selectedRepo.value || !selectedFilePath.value) return
  unstaging.value = true
  saveMessage.value = ''
  try {
    const res = await fetch(
      `${API_BASE}/api/developer/repos/${encodeURIComponent(selectedRepo.value)}/unstage?path=${encodeURIComponent(selectedFilePath.value)}`,
      { method: 'POST', signal: AbortSignal.timeout(6000) },
    )
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    saveMessage.value = 'Unstaged'
    await loadDiff(selectedFilePath.value)
    await fetchRepos()
    await loadRepoStatus(selectedRepo.value)
  } catch {
    saveMessage.value = 'Unstage failed'
  } finally {
    unstaging.value = false
  }
}

async function commitRepo() {
  if (!selectedRepo.value || !commitMessage.value.trim()) return
  committing.value = true
  saveMessage.value = ''
  try {
    if (isDirty.value) {
      await saveCurrentFile()
    }
    const res = await fetch(
      `${API_BASE}/api/developer/repos/${encodeURIComponent(selectedRepo.value)}/commit`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: commitMessage.value.trim() }),
        signal: AbortSignal.timeout(8000),
      },
    )
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const payload = await res.json()
    if (payload.success) {
      saveMessage.value = 'Commit created'
      await loadDiff(selectedFilePath.value)
      await fetchRepos()
      await loadRepoStatus(selectedRepo.value)
    } else {
      saveMessage.value = 'Nothing to commit'
    }
  } catch {
    saveMessage.value = 'Commit failed'
  } finally {
    committing.value = false
  }
}

function refreshDiff() {
  if (!selectedFilePath.value) return
  void loadDiff(selectedFilePath.value)
}

function openReviewTab() {
  dev.setTab('review')
}

onMounted(() => { fetchRepos() })

const filteredRepos = computed(() => {
  const list = repos.value.length > 0 ? repos.value : dev.repos.map(r => ({ name: r.name, path: r.path, branch: r.branch, status: r.status, changes: r.changes, remote: r.remote }))
  if (!filter.value) return list
  const q = filter.value.toLowerCase()
  return list.filter(r => r.name.toLowerCase().includes(q))
})

const filteredFiles = computed(() => {
  if (!fileFilter.value) return files.value
  const q = fileFilter.value.toLowerCase()
  return files.value.filter((f) => String(f.name).toLowerCase().includes(q))
})

const isDirty = computed(() => fileContent.value !== originalFileContent.value)
const canSave = computed(() => !!selectedFilePath.value && isDirty.value && !fileLoading.value)
const fileGitStatusLabel = computed(() => {
  if (fileGitStatus.value === 'added') return 'Added'
  if (fileGitStatus.value === 'deleted') return 'Deleted'
  return 'Modified'
})
</script>

<style scoped>
.developer-panel { max-width: calc(var(--usx-spacing-2xl) * 34); }
.developer-panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--usx-spacing-md); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }
.developer-panel-search { margin-bottom: var(--usx-spacing-md); }
.developer-card-list { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.developer-card { padding: var(--usx-spacing-md); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); border: var(--usx-border-width) solid var(--usx-color-border); }
.developer-card--active { border-color: var(--usx-color-primary); background: color-mix(in srgb, var(--usx-color-primary) 6%, var(--usx-color-surface)); }
.developer-card-header { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.developer-card-title { font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-semibold); flex: 1; }
.developer-card-meta { display: flex; gap: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: var(--usx-spacing-xs); }
.developer-card-remote { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: var(--usx-spacing-sm); }
.developer-card-actions { display: flex; gap: var(--usx-spacing-xs); }

.repos-layout {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.6fr);
  gap: var(--usx-spacing-md);
  min-height: calc(var(--usx-touch-min) * 12);
}

.repos-list-pane,
.repos-editor-pane {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  padding: var(--usx-spacing-md);
  min-width: 0;
}

.repos-editor-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-md);
}

.repos-editor-title {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.repos-editor-subtitle {
  margin: var(--usx-spacing-xs) 0 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.repos-editor-actions {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.repos-editor-content {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.7fr);
  gap: var(--usx-spacing-md);
  min-height: calc(var(--usx-touch-min) * 8);
}

.repo-files-panel,
.repo-editor-panel {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-background);
  min-width: 0;
}

.repo-files-panel {
  display: flex;
  flex-direction: column;
}

.repo-files-search {
  margin: var(--usx-spacing-sm);
}

.repo-files-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: 0 var(--usx-spacing-sm) var(--usx-spacing-sm);
  overflow: auto;
  align-items: stretch;
}

.repo-file-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--usx-spacing-xs);
  width: 100%;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid transparent;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  text-align: left;
  cursor: pointer;
}

.repo-status-groups {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: 0 var(--usx-spacing-sm) var(--usx-spacing-sm);
}

.repo-status-group {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
}

.repo-status-group-title {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.repo-status-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--usx-spacing-xs);
  width: 100%;
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  text-align: left;
  cursor: pointer;
}

.repo-status-item:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
}

.repo-file-item:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}

.repo-file-item--active {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
}

.repo-files-empty,
.repo-editor-empty,
.repos-editor-empty {
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.repo-editor-wrap {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.repo-editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.repo-editor-toolbar-actions {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.repo-editor {
  flex: 1;
  min-height: calc(var(--usx-touch-min) * 6);
  border: none;
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-sm);
  resize: vertical;
}

.repo-editor-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.repo-editor-dirty {
  color: var(--usx-color-warning);
}

.repo-diff-panel {
  border-top: var(--usx-border-width) solid var(--usx-color-border);
}

.repo-diff-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.repo-diff-content {
  margin: 0;
  max-height: calc(var(--usx-touch-min) * 4);
  overflow: auto;
  padding: var(--usx-spacing-sm);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-mono);
  white-space: pre;
}

.repo-commit-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--usx-spacing-sm);
  align-items: center;
  padding: var(--usx-spacing-sm);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
}

.repo-commit-input {
  min-height: var(--usx-touch-min);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
}

@media (max-width: calc(var(--usx-spacing-2xl) * 26)) {
  .repos-layout,
  .repos-editor-content {
    grid-template-columns: 1fr;
  }
}
</style>