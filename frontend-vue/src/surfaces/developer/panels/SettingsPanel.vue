<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Developer Settings</h3>
      <p class="developer-panel-desc">Global, USX, GridCore, and uSystem configuration layers.</p>
    </div>

    <!-- Layer Tabs -->
    <div class="settings-layers">
      <button v-for="layer in layers" :key="layer.id" class="settings-layer-tab" :class="{ 'settings-layer-tab--active': activeLayer === layer.id }" @click="activeLayer = layer.id">{{ layer.label }}</button>
    </div>

    <!-- Layer 1: Global Settings -->
    <div v-if="activeLayer === 'global'" class="settings-group">
      <h4 class="settings-group-title">Global Settings</h4>
      <div class="settings-row">
        <label>Font Style</label>
        <select v-model="global.fontStyle">
          <option value="inter">Inter</option>
          <option value="system">System</option>
          <option value="mono">Mono</option>
        </select>
      </div>
      <div class="settings-row">
        <label>Base Font Size</label>
        <input type="range" v-model.number="global.fontSize" min="12" max="24" />
        <span>{{ global.fontSize }}px</span>
      </div>
      <div class="settings-row">
        <label>Color Palette</label>
        <select v-model="global.palette">
          <option value="default">Default</option>
          <option value="ocean">Ocean</option>
          <option value="forest">Forest</option>
          <option value="sunset">Sunset</option>
        </select>
      </div>
      <div class="settings-row">
        <label>Theme Mode</label>
        <select v-model="global.themeMode">
          <option value="light">Light</option>
          <option value="dark">Dark</option>
          <option value="auto">Auto (System)</option>
        </select>
      </div>
    </div>

    <!-- Layer 2: USX Settings -->
    <div v-if="activeLayer === 'usx'" class="settings-group">
      <h4 class="settings-group-title">USX Settings</h4>
      <div class="settings-row">
        <label>Typography Scale</label>
        <select v-model="usx.typographyScale">
          <option value="compact">Compact</option>
          <option value="normal">Normal</option>
          <option value="spacious">Spacious</option>
        </select>
      </div>
      <div class="settings-row">
        <label>Line Height</label>
        <input type="range" v-model.number="usx.lineHeight" min="1.0" max="2.0" step="0.1" />
        <span>{{ usx.lineHeight }}</span>
      </div>
      <div class="settings-row">
        <label>Border Radius</label>
        <select v-model="usx.borderRadius">
          <option value="sharp">Sharp</option>
          <option value="rounded">Rounded</option>
          <option value="pill">Pill</option>
        </select>
      </div>
    </div>

    <!-- Layer 3: GridCore Settings -->
    <div v-if="activeLayer === 'gridcore'" class="settings-group">
      <h4 class="settings-group-title">GridCore Settings</h4>
      <div class="settings-row">
        <label>Preset</label>
        <select v-model="gridcore.preset">
          <option value="compact">Compact</option>
          <option value="normal">Normal</option>
          <option value="spacious">Spacious</option>
          <option value="hd">HD</option>
          <option value="retro">Retro</option>
        </select>
      </div>
      <div class="settings-row">
        <label>Cell Width</label>
        <input type="range" v-model.number="gridcore.cellWidth" min="6" max="20" />
        <span>{{ gridcore.cellWidth }}px</span>
      </div>
      <div class="settings-row">
        <label>Cell Height</label>
        <input type="range" v-model.number="gridcore.cellHeight" min="10" max="32" />
        <span>{{ gridcore.cellHeight }}px</span>
      </div>
      <div class="settings-row">
        <label>Render Mode</label>
        <select v-model="gridcore.renderMode">
          <option value="canvas">Canvas</option>
          <option value="dom">DOM</option>
          <option value="hybrid">Hybrid</option>
        </select>
      </div>
    </div>

    <!-- Layer 4: uSystem Settings -->
    <div v-if="activeLayer === 'usystem'" class="settings-group">
      <h4 class="settings-group-title">uSystem Settings</h4>
      <div class="settings-row">
        <label>Backend URL</label>
        <input type="text" v-model="usystem.serviceUrl" class="settings-input" />
      </div>
      <div class="settings-row">
        <label>Auto-refresh (seconds)</label>
        <input type="number" v-model.number="usystem.refreshInterval" min="5" max="300" />
      </div>
      <div class="settings-row">
        <label>Debug Logs</label>
        <input type="checkbox" v-model="usystem.enableDebugLogs" />
      </div>
      <div class="settings-row">
        <label>Enable Metrics</label>
        <input type="checkbox" v-model="usystem.enableMetrics" />
      </div>
    </div>

    <!-- Agent Behavior (Common) -->
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
import { reactive, ref, watch } from 'vue'
import { useGridCoreSettingsStore } from '../../../stores/gridcoreSettings'

type SettingsLayer = 'global' | 'usx' | 'gridcore' | 'usystem'

const layers: Array<{ id: SettingsLayer; label: string }> = [
  { id: 'global', label: 'Global' },
  { id: 'usx', label: 'USX' },
  { id: 'gridcore', label: 'GridCore' },
  { id: 'usystem', label: 'uSystem' },
]

const activeLayer = ref<SettingsLayer>('global')
const gridcore = useGridCoreSettingsStore()

const global = reactive({
  fontStyle: 'inter',
  fontSize: 16,
  palette: 'default',
  themeMode: 'dark',
})

const usx = reactive({
  typographyScale: 'normal',
  lineHeight: 1.5,
  borderRadius: 'rounded',
})

const usystem = reactive({
  serviceUrl: 'http://localhost:8333',
  refreshInterval: 30,
  enableDebugLogs: false,
  enableMetrics: true,
})

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
.developer-panel { max-width: calc(var(--usx-spacing-2xl) * 19); }
.developer-panel-header { margin-bottom: var(--usx-spacing-lg); }
.developer-panel-title { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); margin: 0; }

.settings-group { margin-bottom: var(--usx-spacing-lg); }
.settings-group-title { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-semibold); text-transform: uppercase; letter-spacing: 0.03em; color: var(--usx-color-on-surface-muted); margin: 0 0 var(--usx-spacing-sm); }

.settings-row { display: flex; align-items: center; gap: var(--usx-spacing-md); padding: var(--usx-spacing-sm) 0; }
.settings-row label { flex: 1; font-size: var(--usx-font-size-sm); }
.settings-row select,
.settings-row input[type="number"] { padding: var(--usx-spacing-xs) var(--usx-spacing-sm); background: var(--usx-color-background); border-radius: var(--usx-radius-sm); color: var(--usx-color-on-surface); font-size: var(--usx-font-size-sm); }
.settings-row input[type="range"] { flex: 1; }
.settings-row input[type="checkbox"] { width: var(--usx-spacing-lg); height: var(--usx-spacing-lg); }
</style>