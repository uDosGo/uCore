<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="SYSTEM_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content">
      <!-- Pages Browser -->
      <div v-if="currentTab === 'pages'">
        <h3 class="surface__panel-title">System Pages</h3>
        <p class="usx-mb-md" style="font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted)">Browse S-pages and P-pages.</p>
        <div class="system-pages-grid">
          <div v-for="page in sPages" :key="page.id" class="system-page-card">
            <UIcon :name="page.icon" />
            <span class="system-page-id">{{ page.id }}</span>
            <span class="system-page-title">{{ page.title }}</span>
          </div>
        </div>
      </div>

      <!-- Tools -->
      <div v-else-if="currentTab === 'tools'">
        <h3 class="surface__panel-title">System Tools</h3>
        <div class="system-tools-grid">
          <div v-for="tool in tools" :key="tool.id" class="system-tool-card">
            <UIcon :name="tool.icon" />
            <span class="system-tool-name">{{ tool.name }}</span>
            <span class="system-tool-desc">{{ tool.description }}</span>
          </div>
        </div>
      </div>

      <!-- Services -->
      <div v-else-if="currentTab === 'services'">
        <h3 class="surface__panel-title">Services</h3>
        <div class="system-services-list">
          <div v-for="svc in services" :key="svc.name" class="system-service-row">
            <span class="system-service-dot" :class="'system-service-dot--' + svc.status" />
            <span class="system-service-name">{{ svc.name }}</span>
            <span class="system-service-desc">{{ svc.description }}</span>
            <UBadge :type="svc.status === 'up' ? 'success' : 'error'" size="sm">{{ svc.status }}</UBadge>
          </div>
        </div>
      </div>

      <!-- Variables -->
      <div v-else-if="currentTab === 'variables'">
        <h3 class="surface__panel-title">System Variables</h3>
        <div v-if="loadingVars" class="system-loading">Loading variables...</div>
        <div v-else class="system-vars-list">
          <div v-for="v in variables" :key="v.key" class="system-var-row">
            <code class="system-var-key">{{ v.key }}</code>
            <span class="system-var-value">{{ v.value }}</span>
            <UBadge type="info" size="sm">{{ v.scope }}</UBadge>
          </div>
        </div>
      </div>

      <!-- Secrets -->
      <div v-else-if="currentTab === 'secrets'">
        <h3 class="surface__panel-title">Secrets</h3>
        <p class="usx-mb-md" style="font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted)">Encrypted secret storage. Values are masked.</p>
        <div v-if="loadingSecrets" class="system-loading">Loading secrets...</div>
        <div v-else class="system-secrets-list">
          <div v-for="secret in secrets" :key="secret.key" class="system-secret-row">
            <span class="system-secret-key">{{ secret.key }}</span>
            <span class="system-secret-value">••••••••</span>
            <UBadge type="info" size="sm">{{ secret.scope }}</UBadge>
          </div>
        </div>
      </div>

      <!-- Global Settings -->
      <div v-else-if="currentTab === 'global-settings'">
        <h3 class="surface__panel-title">Global Settings</h3>
        <div class="system-settings-form">
          <div class="settings-row"><label>Theme</label><select v-model="themeSettings.theme"><option>dark</option><option>light</option><option>auto</option></select></div>
          <div class="settings-row"><label>Font Size</label><input type="range" min="12" max="24" v-model.number="themeSettings.fontSize" /><span>{{ themeSettings.fontSize }}px</span></div>
          <div class="settings-row"><label>Palette</label><select v-model="themeSettings.palette"><option>default</option><option>ocean</option><option>forest</option><option>sunset</option></select></div>
        </div>
      </div>

      <!-- User Settings -->
      <div v-else-if="currentTab === 'user-settings'">
        <h3 class="surface__panel-title">User Settings</h3>
        <div class="system-settings-form">
          <div class="settings-row"><label>Display Name</label><input type="text" v-model="userSettings.displayName" /></div>
          <div class="settings-row"><label>Email</label><input type="email" v-model="userSettings.email" placeholder="user@example.com" /></div>
          <div class="settings-row"><label>Default Model</label><select v-model="userSettings.defaultModel"><option>Llama 3.2</option><option>GPT-4o</option><option>DeepSeek V3</option></select></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
/**
 * Separated from <script setup> to allow named exports.
 */
import type { TabDef } from '../../skills/molecules/SurfaceTabNav.vue'

export const SYSTEM_TABS: TabDef[] = [
  { id: 'pages', label: 'Pages', icon: 'dashboard' },
  { id: 'tools', label: 'Tools', icon: 'build' },
  { id: 'services', label: 'Services', icon: 'dns' },
  { id: 'variables', label: 'Variables', icon: 'tune' },
  { id: 'secrets', label: 'Secrets', icon: 'key' },
  { id: 'global-settings', label: 'Global', icon: 'settings' },
  { id: 'user-settings', label: 'User', icon: 'person' },
]
</script>

<script setup lang="ts">
import { computed, ref, reactive, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useShellStore } from '../../stores/shell'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'
const route = useRoute()
const shell = useShellStore()

const activeTab = ref((route.query.tab as string) || 'pages')
const currentTab = computed(() => activeTab.value)
const loadingVars = ref(true)
const loadingSecrets = ref(true)

const sPages = [
  { id: 'S100', title: 'Tool Builder', icon: 'build' },
  { id: 'S101', title: 'Story Builder', icon: 'auto_stories' },
  { id: 'S300', title: 'Workflow Builder', icon: 'account_tree' },
  { id: 'S310', title: 'Clipboard Orchestration', icon: 'content_paste' },
  { id: 'S320', title: 'Knowledge Tools', icon: 'psychology' },
  { id: 'S330', title: 'Migration Dashboard', icon: 'migration' },
  { id: 'S600', title: 'Learning Hub', icon: 'school' },
]

const tools = [
  { id: 'tool-builder', name: 'Tool Builder', icon: 'build', description: 'Create and edit system tools' },
  { id: 'story-builder', name: 'Story Builder', icon: 'auto_stories', description: 'Build narrative content' },
  { id: 'workflow-builder', name: 'Workflow Builder', icon: 'account_tree', description: 'Design automation workflows' },
  { id: 'clipboard-ops', name: 'Clipboard Ops', icon: 'content_paste', description: 'Clipboard buffer management' },
]

interface ServiceItem { name: string; status: string; description: string }
interface VariableItem { key: string; value: string; scope: string }
interface SecretItem { key: string; scope: string }

const services = ref<ServiceItem[]>([])
const variables = ref<VariableItem[]>([])
const secrets = ref<SecretItem[]>([])

const themeSettings = reactive({ theme: 'dark', fontSize: 16, palette: 'default' })
const userSettings = reactive({ displayName: 'uDos Developer', email: '', defaultModel: 'Llama 3.2' })

// Persist theme/user settings
watch(themeSettings, (v) => { try { localStorage.setItem('ucore-theme-settings', JSON.stringify(v)) } catch {} }, { deep: true })
watch(userSettings, (v) => { try { localStorage.setItem('ucore-user-settings', JSON.stringify(v)) } catch {} }, { deep: true })

function loadSettings() {
  try {
    const t = localStorage.getItem('ucore-theme-settings')
    if (t) Object.assign(themeSettings, JSON.parse(t))
    const u = localStorage.getItem('ucore-user-settings')
    if (u) Object.assign(userSettings, JSON.parse(u))
  } catch {}
}

async function fetchSystemData() {
  // Services — health checks
  try {
    const checks = [
      (async () => ({ name: 'snackbar', status: await ping(8484) ? 'up' : 'down', description: 'Container orchestrator' }))(),
      (async () => ({ name: 'hivemind', status: await ping(8490) ? 'up' : 'down', description: 'AI agent routing' }))(),
      (async () => ({ name: 'vault-mcp', status: await ping(8765) ? 'up' : 'down', description: 'Vault MCP bridge' }))(),
      (async () => ({ name: 'email-feed', status: 'down', description: 'Email processor (not running)' }))(),
    ]
    services.value = await Promise.all(checks)
  } catch {}

  // Variables
  loadingVars.value = true
  try {
    const res = await fetch(`${API_BASE}/api/variables`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      const list = data.variables || data || []
      variables.value = Object.entries(list).map(([key, value]: [string, any]) => ({
        key,
        value: typeof value === 'string' ? value : JSON.stringify(value),
        scope: key.startsWith('VITE_') ? 'global' : 'system',
      }))
    }
  } catch {}
  loadingVars.value = false

  // Secrets
  loadingSecrets.value = true
  try {
    const res = await fetch(`${API_BASE}/api/secrets`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      const list = data.secrets || data || []
      secrets.value = Array.isArray(list) ? list.map((s: any) => ({ key: s.key || s.name, scope: s.scope || 'user' })) : []
    }
  } catch {}
  loadingSecrets.value = false

  // Load persisted settings
  loadSettings()
}

async function ping(port: number): Promise<boolean> {
  try {
    const res = await fetch(`http://localhost:${port}/health`, { signal: AbortSignal.timeout(1500) })
    return res.ok
  } catch { return false }
}

onMounted(() => { fetchSystemData() })
</script>

<style scoped>
.system-pages-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: var(--usx-spacing-sm); }
.system-page-card { display: flex; flex-direction: column; align-items: center; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-md); background: var(--pico-card-background-color); border-radius: var(--usx-border-radius-lg); cursor: pointer; transition: all 0.15s ease; }
.system-page-card:hover { border-color: var(--pico-primary); }
.system-page-id { font-size: var(--usx-font-size-sm); font-weight: 600; color: var(--pico-primary); }
.system-page-title { font-size: var(--usx-font-size-sm); text-align: center; }
.system-tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--usx-spacing-sm); }
.system-tool-card { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-md); background: var(--pico-card-background-color); border-radius: var(--usx-border-radius-lg); }
.system-tool-name { font-size: var(--usx-font-size-base); font-weight: 600; }
.system-tool-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.system-services-list { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); }
.system-service-row { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); background: var(--pico-background-color); border-radius: var(--usx-border-radius-md); }
.system-service-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.system-service-dot--up { background: #3fb950; }
.system-service-dot--degraded { background: #d29922; }
.system-service-dot--down { background: #f85149; }
.system-service-name { font-size: var(--usx-font-size-sm); font-weight: 500; min-width: 100px; }
.system-service-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); flex: 1; }
.system-vars-list { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); }
.system-var-row { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); border-radius: var(--usx-border-radius-sm); }
.system-var-key { font-family: monospace; font-size: var(--usx-font-size-sm); color: var(--pico-primary); min-width: 160px; }
.system-var-value { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); flex: 1; }
.system-secrets-list { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); }
.system-secret-row { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); border-radius: var(--usx-border-radius-sm); }
.system-secret-key { font-size: var(--usx-font-size-sm); font-weight: 500; min-width: 160px; }
.system-secret-value { font-family: monospace; font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); flex: 1; }
.system-settings-form { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.settings-row { display: flex; align-items: center; gap: var(--usx-spacing-md); padding: var(--usx-spacing-sm) 0; }
.settings-row label { min-width: 120px; font-size: var(--usx-font-size-sm); }
.settings-row select, .settings-row input[type="text"], .settings-row input[type="email"] { padding: var(--usx-spacing-xs) var(--usx-spacing-sm); background: var(--pico-background-color); border-radius: var(--usx-border-radius-sm); color: var(--pico-color); font-size: var(--usx-font-size-sm); }
.system-loading { padding: var(--usx-spacing-lg); text-align: center; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }
</style>