<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">DocLang Bridge</h3>
      <p class="developer-panel-desc">Export vault markdown into DocLang + AI context JSONL format.</p>
    </div>

    <div class="settings-group">
      <h4 class="settings-group-title">Export Configuration</h4>
      <div class="settings-row">
        <label>Source Directory</label>
        <input
          v-model="sourceDir"
          type="text"
          placeholder="~/vault/docs or /path/to/markdown"
          class="settings-input"
        />
      </div>
      <div class="settings-row">
        <label>Output Path</label>
        <input
          v-model="outputPath"
          type="text"
          placeholder="~/tmp/doclang-context.jsonl"
          class="settings-input"
        />
      </div>
      <div class="settings-row">
        <label>Extra Tags (comma-separated)</label>
        <input
          v-model="extraTags"
          type="text"
          placeholder="vault,export"
          class="settings-input"
        />
      </div>
    </div>

    <div class="settings-row">
      <button class="usx-btn usx-btn--primary" :disabled="exporting" @click="runExport">
        <UIcon v-if="exporting" name="sync" spin />
        <UIcon v-else name="file_download" />
        {{ exporting ? 'Exporting...' : 'Export DocLang JSONL' }}
      </button>
      <button class="usx-btn" :disabled="exporting" @click="runPreview">
        <UIcon name="preview" />
        Preview First Document
      </button>
    </div>

    <div v-if="lastResult" class="export-result">
      <h4>Last Export</h4>
      <pre class="export-meta">{{ JSON.stringify(lastResult, null, 2) }}</pre>
    </div>

    <div v-if="previewData" class="preview-section">
      <h4>Preview: {{ previewData.title }}</h4>
      <div class="preview-meta">
        <span class="doc-badge doc-badge--type">{{ previewData.doc_type }}</span>
        <span class="doc-badge doc-badge--status">{{ previewData.status }}</span>
        <span v-for="tag in previewData.tags?.slice(0, 5)" :key="tag" class="doc-badge">{{ tag }}</span>
      </div>
      <h5>Sections</h5>
      <ul class="section-list">
        <li v-for="s in previewData.sections" :key="s.id">
          <strong>{{ s.heading || '(untitled)' }}</strong>
          <span class="section-level">L{{ s.level }}</span>
          <p class="section-snippet">{{ s.content?.slice(0, 200) }}{{ s.content?.length > 200 ? '...' : '' }}</p>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'

interface DocLangSection {
  id: string
  heading: string
  level: number
  content: string
}

interface DocLangPreview {
  title: string
  doc_type: string
  status: string
  tags?: string[]
  sections: DocLangSection[]
}

interface DocLangResponse {
  preview?: DocLangPreview
}

const SNACKBAR_API = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

const sourceDir = ref('~/Code/uCore/docs')
const outputPath = ref('~/tmp/doclang-context.jsonl')
const extraTags = ref('')
const exporting = ref(false)
const lastResult = ref<Record<string, unknown> | null>(null)
const previewData = ref<DocLangPreview | null>(null)

async function runExport() {
  exporting.value = true
  lastResult.value = null
  try {
    // Run via the export script endpoint (or call the Python module directly via MCP)
    const tags = extraTags.value.split(',').map(t => t.trim()).filter(Boolean)
    const res = await fetch(`${SNACKBAR_API}/api/skills/doclang_export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        params: {
          source_dir: sourceDir.value.replace(/^~/, '/Users/fredbook'),
          output_path: outputPath.value.replace(/^~/, '/Users/fredbook'),
          tags: tags.length > 0 ? tags : undefined,
        },
      }),
      signal: AbortSignal.timeout(30000),
    })
    lastResult.value = await res.json()
  } catch (e: any) {
    lastResult.value = { error: e.message }
  } finally {
    exporting.value = false
  }
}

async function runPreview() {
  previewData.value = null
  try {
    // Fetch first doc directly via a quick export
    const res = await fetch(`${SNACKBAR_API}/api/skills/doclang_export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        params: {
          source_dir: sourceDir.value.replace(/^~/, '/Users/fredbook'),
          output_path: '/tmp/doclang-preview.jsonl',
          tags: [],
          preview: true,
        },
      }),
      signal: AbortSignal.timeout(10000),
    })
    const data = (await res.json()) as DocLangResponse
    if (data.preview) {
      previewData.value = data.preview
    }
  } catch (e: any) {
    previewData.value = {
      title: 'Error',
      doc_type: 'error',
      status: 'error',
      sections: [
        { id: 'error', heading: 'Error', content: e.message, level: 1 },
      ],
    }
  }
}
</script>

<style scoped>
.developer-panel { max-width: 800px; }
.developer-panel-header { margin-bottom: var(--usx-spacing-lg); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }
.developer-panel-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-top: var(--usx-spacing-xs); }

.settings-group { margin-bottom: var(--usx-spacing-lg); }
.settings-group-title { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-semibold); text-transform: uppercase; letter-spacing: 0.5px; color: var(--usx-color-on-surface-muted); margin: 0 0 var(--usx-spacing-sm); }

.settings-row { display: flex; align-items: center; gap: var(--usx-spacing-md); padding: var(--usx-spacing-sm) 0; flex-wrap: wrap; }
.settings-row label { flex: 0 0 140px; font-size: var(--usx-font-size-sm); }
.settings-input { flex: 1; padding: var(--usx-spacing-xs) var(--usx-spacing-sm); background: var(--usx-color-background); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); color: var(--usx-color-on-surface); font-size: var(--usx-font-size-sm); font-family: var(--usx-font-family-mono); }

.export-result { margin-top: var(--usx-spacing-lg); }
.export-meta { background: var(--usx-color-surface-variant); padding: var(--usx-spacing-md); border-radius: var(--usx-radius-sm); font-size: var(--usx-font-size-xs); font-family: var(--usx-font-family-mono); overflow-x: auto; }

.preview-section { margin-top: var(--usx-spacing-lg); background: var(--usx-color-surface); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); padding: var(--usx-spacing-md); }
.preview-meta { display: flex; gap: var(--usx-spacing-xs); flex-wrap: wrap; margin-bottom: var(--usx-spacing-md); }
.doc-badge { padding: 2px 8px; background: var(--usx-color-surface-variant); border-radius: var(--usx-radius-sm); font-size: var(--usx-font-size-xs); }
.doc-badge--type { background: var(--usx-color-primary-disabled); color: var(--usx-color-primary); }
.doc-badge--status { background: var(--usx-color-success); color: var(--usx-color-on-success); }
.section-list { list-style: none; padding: 0; margin: 0; }
.section-list li { margin-bottom: var(--usx-spacing-sm); }
.section-level { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); margin-left: var(--usx-spacing-xs); }
.section-snippet { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-top: 2px; }

.usx-btn { padding: var(--usx-spacing-sm) var(--usx-spacing-md); border-radius: var(--usx-radius-md); display: inline-flex; align-items: center; gap: var(--usx-spacing-xs); border: var(--usx-border-width) solid var(--usx-color-border); background: transparent; color: var(--usx-color-on-surface); cursor: pointer; font-family: var(--usx-font-family-sans); font-size: var(--usx-font-size-sm); }
.usx-btn--primary { background: var(--usx-color-primary); border-color: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.usx-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>