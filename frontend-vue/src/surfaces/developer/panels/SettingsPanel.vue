<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Developer Settings</h3>
    </div>

    <div class="settings-group">
      <h4 class="settings-group-title">Model Defaults</h4>
      <div class="settings-row">
        <label>Default Model</label>
        <select v-model="settings.defaultModel">
          <option value="llama3.2">Llama 3.2 (ollama)</option>
          <option value="mistral">Mistral (ollama)</option>
          <option value="gpt-4o">GPT-4o (openrouter)</option>
          <option value="deepseek-v3">DeepSeek V3 (openrouter)</option>
        </select>
      </div>
      <div class="settings-row">
        <label>Temperature</label>
        <input type="range" v-model.number="settings.temperature" min="0" max="2" step="0.1" />
        <span>{{ settings.temperature }}</span>
      </div>
    </div>

    <div class="settings-group">
      <h4 class="settings-group-title">Agent Behavior</h4>
      <div class="settings-row">
        <label>Auto-save conversations</label>
        <input type="checkbox" v-model="settings.autoSave" />
      </div>
      <div class="settings-row">
        <label>Stream responses</label>
        <input type="checkbox" v-model="settings.streaming" />
      </div>
      <div class="settings-row">
        <label>Show prompt cards</label>
        <input type="checkbox" v-model="settings.showPrompts" />
      </div>
    </div>

    <div class="settings-group">
      <h4 class="settings-group-title">Review Preferences</h4>
      <div class="settings-row">
        <label>Default repo</label>
        <select v-model="settings.defaultRepo">
          <option value="uCore">uCore</option>
          <option value="uConnect">uConnect</option>
          <option value="uServer">uServer</option>
        </select>
      </div>
      <div class="settings-row">
        <label>Diff context lines</label>
        <input type="number" v-model.number="settings.diffContext" min="1" max="20" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component SettingsPanel
 * @description Developer preferences — model defaults, agent behavior, review settings.
 * Persisted via localStorage.
 * @category surfaces/developer
 */
import { reactive, watch } from 'vue'

const STORAGE_KEY = 'ucore-dev-settings'

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const saved = JSON.parse(raw)
      return {
        defaultModel: saved.defaultModel || 'llama3.2',
        temperature: saved.temperature ?? 0.7,
        autoSave: saved.autoSave !== false,
        streaming: saved.streaming !== false,
        showPrompts: saved.showPrompts !== false,
        defaultRepo: saved.defaultRepo || 'uCore',
        diffContext: saved.diffContext || 3,
      }
    }
  } catch {
    // Fall through to defaults
  }
  return {
    defaultModel: 'llama3.2',
    temperature: 0.7,
    autoSave: true,
    streaming: true,
    showPrompts: true,
    defaultRepo: 'uCore',
    diffContext: 3,
  }
}

const settings = reactive(loadSettings())

// Auto-persist on any change
watch(settings, (val) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
  } catch {
    // Storage full or unavailable — silent
  }
}, { deep: true })
</script>

<style scoped>
.developer-panel { max-width: 600px; }
.developer-panel-header { margin-bottom: var(--usx-spacing-lg); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }

.settings-group { margin-bottom: var(--usx-spacing-lg); }
.settings-group-title { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-semibold); text-transform: uppercase; letter-spacing: 0.5px; color: var(--usx-color-on-surface-muted); margin: 0 0 var(--usx-spacing-sm); }

.settings-row { display: flex; align-items: center; gap: var(--usx-spacing-md); padding: var(--usx-spacing-sm) 0; }
.settings-row label { flex: 1; font-size: var(--usx-font-size-sm); }
.settings-row select,
.settings-row input[type="number"] { padding: var(--usx-spacing-xs) var(--usx-spacing-sm); background: var(--usx-color-background); border-radius: var(--usx-radius-sm); color: var(--usx-color-on-surface); font-size: var(--usx-font-size-sm); }
.settings-row input[type="range"] { flex: 1; }
.settings-row input[type="checkbox"] { width: 16px; height: 16px; }
</style>