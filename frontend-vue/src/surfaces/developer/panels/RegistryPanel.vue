<template>
  <div class="registry-panel">
    <!-- Left Sidebar — half-column sub-tabs -->
    <div class="registry-sidebar">
      <h3 class="registry-sidebar__title">Ecosystem Registry</h3>

      <div class="registry-sidebar__tabs">
        <button
          v-for="tab in subTabs"
          :key="tab.id"
          class="registry-sidebar__tab"
          :class="{ 'registry-sidebar__tab--active': activeSubTab === tab.id }"
          @click="activeSubTab = tab.id"
        >
          <span class="material-symbols-outlined">{{ tab.icon }}</span>
          <span class="registry-sidebar__tab-label">{{ tab.label }}</span>
          <span class="registry-sidebar__tab-count">{{ tab.count }}</span>
        </button>
      </div>

      <!-- Repo Filter -->
      <div class="registry-sidebar__filter">
        <select v-model="repoFilter" style="width: 100%; min-height: var(--usx-touch-min-sm); padding: 0 var(--usx-spacing-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface); color: var(--usx-color-on-surface); font-size: var(--usx-font-size-sm); font-family: var(--usx-font-family-sans)">
          <option value="">All Repos</option>
          <option v-for="repo in repos" :key="repo" :value="repo">{{ repo }}</option>
        </select>
      </div>

      <div class="registry-sidebar__summary">
        <span style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)">
          Total: {{ totalItems }} items across {{ subTabs.length }} registries
        </span>
        <span v-if="repoFilter" style="font-size: var(--usx-font-size-xs); color: var(--usx-color-primary); display: block" class="usx-mt-sm">
          Filtered: {{ repoFilter }}
        </span>
      </div>
    </div>

    <!-- Right Content Area -->
    <div class="registry-content">
      <!-- Summary Cards -->
      <div class="registry-summary-cards">
        <div
          v-for="tab in subTabs"
          :key="tab.id"
          class="usx-card registry-summary-card"
          :class="{ 'registry-summary-card--active': activeSubTab === tab.id }"
          @click="activeSubTab = tab.id"
        >
          <span class="material-symbols-outlined">{{ tab.icon }}</span>
          <span style="font-weight: var(--usx-font-weight-semibold)">{{ tab.count }}</span>
          <span style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)">{{ tab.label }}</span>
        </div>
      </div>

      <!-- Search -->
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search registry..."
        class="registry-search"
      />

      <!-- Skills View -->
      <div v-if="activeSubTab === 'skills'" class="registry-view">
        <h4>Skills ({{ filteredSkills.length }})</h4>
        <div v-if="filteredSkills.length === 0" class="usx-compact" style="text-align: center; color: var(--usx-color-on-surface-muted)">
          No skills match your search.
        </div>
        <div v-else class="registry-grid">
          <div v-for="skill in filteredSkills" :key="skill.skill_id" class="usx-card registry-card">
            <div class="usx-flex-between">
              <span style="font-weight: var(--usx-font-weight-semibold)">{{ skill.name }}</span>
              <span class="usx-badge registry-badge--xs">{{ skill.category }}</span>
            </div>
            <div style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)" class="usx-mt-sm">
              {{ skill.description || skill.skill_id }}
            </div>
            <div class="usx-flex-row usx-gap-xs usx-mt-sm" style="flex-wrap: wrap; font-size: var(--usx-font-size-xs)">
              <span v-if="skill.params.length" class="usx-badge registry-badge--compact">
                {{ skill.params.length }} params
              </span>
              <span class="usx-badge registry-badge--compact">
                {{ skill.timeout }}s timeout
              </span>
              <span v-if="skill.requires_confirmation" class="usx-badge usx-badge--accent registry-badge--compact">
                confirmation
              </span>
              <span style="color: var(--usx-color-on-surface-muted)">{{ skill.file }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Paths View -->
      <div v-if="activeSubTab === 'paths'" class="registry-view">
        <h4>Paths ({{ filteredPaths.length }})</h4>
        <div v-if="filteredPaths.length === 0" class="usx-compact" style="text-align: center; color: var(--usx-color-on-surface-muted)">
          No paths match your search.
        </div>
        <div v-else class="registry-grid">
          <div v-for="path in filteredPaths" :key="path.path" class="usx-card registry-card">
            <div class="usx-flex-between">
              <span style="font-weight: var(--usx-font-weight-medium); font-family: var(--usx-font-family-mono); font-size: var(--usx-font-size-sm)">
                {{ path.path }}
              </span>
              <span class="usx-badge registry-badge--xs">{{ path.type }}</span>
            </div>
            <div style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)" class="usx-mt-sm">
              {{ path.description }}
            </div>
          </div>
        </div>
      </div>

      <!-- Variables View -->
      <div v-if="activeSubTab === 'variables'" class="registry-view">
        <h4>Variables ({{ filteredVariables.length }})</h4>
        <div v-if="filteredVariables.length === 0" class="usx-compact" style="text-align: center; color: var(--usx-color-on-surface-muted)">
          No variables match your search.
        </div>
        <div v-else class="registry-grid">
          <div v-for="v in filteredVariables" :key="v.scope" class="usx-card registry-card">
            <div class="usx-flex-between">
              <span style="font-weight: var(--usx-font-weight-semibold)">{{ v.scope }}</span>
            </div>
            <div style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)" class="usx-mt-sm">
              {{ v.description }}
            </div>
            <div class="usx-flex-row usx-gap-xs usx-mt-sm" style="flex-wrap: wrap">
              <span v-if="v.file" class="usx-badge registry-badge--compact registry-badge--mono">
                {{ v.file }}
              </span>
              <span v-if="v.examples?.length" class="usx-badge usx-badge--accent registry-badge--compact">
                {{ v.examples.length }} examples
              </span>
            </div>
            <div v-if="v.examples?.length" class="usx-flex-row usx-gap-xs usx-mt-sm" style="flex-wrap: wrap">
              <span v-for="ex in v.examples" :key="ex" class="usx-badge registry-badge--compact registry-badge--mono">
                {{ ex }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Secrets View -->
      <div v-if="activeSubTab === 'secrets'" class="registry-view">
        <h4>Secrets ({{ filteredSecrets.length }})</h4>
        <div v-if="filteredSecrets.length === 0" class="usx-compact" style="text-align: center; color: var(--usx-color-on-surface-muted)">
          No secrets match your search.
        </div>
        <div v-else class="registry-grid">
          <div v-for="s in filteredSecrets" :key="s.key" class="usx-card registry-card">
            <div class="usx-flex-between">
              <span style="font-weight: var(--usx-font-weight-medium); font-family: var(--usx-font-family-mono)">
                {{ s.key }}
              </span>
              <span class="usx-badge registry-badge--xs">{{ s.scope }}</span>
            </div>
            <div style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)" class="usx-mt-sm">
              {{ s.description || s.store }}
            </div>
          </div>
        </div>
      </div>

      <!-- MCP Servers View -->
      <div v-if="activeSubTab === 'mcp'" class="registry-view">
        <h4>MCP Servers ({{ filteredMcp.length }})</h4>
        <div v-if="filteredMcp.length === 0" class="usx-compact" style="text-align: center; color: var(--usx-color-on-surface-muted)">
          No MCP servers match your search.
        </div>
        <div v-else class="registry-grid">
          <div v-for="m in filteredMcp" :key="m.name" class="usx-card registry-card">
            <div class="usx-flex-between">
              <span style="font-weight: var(--usx-font-weight-semibold)">{{ m.name }}</span>
              <span v-if="m.disabled" class="usx-badge usx-badge--error registry-badge--xs">disabled</span>
              <span v-else class="usx-badge usx-badge--success registry-badge--xs">active</span>
            </div>
            <div style="font-size: var(--usx-font-size-xs); font-family: var(--usx-font-family-mono); color: var(--usx-color-on-surface-muted)" class="usx-mt-sm">
              {{ m.command }}
            </div>
            <div style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)" class="usx-mt-sm">
              cwd: {{ m.cwd || m.file || '—' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Routes View -->
      <div v-if="activeSubTab === 'routes'" class="registry-view">
        <h4>Routes ({{ filteredRoutes.length }})</h4>
        <div v-if="filteredRoutes.length === 0" class="usx-compact" style="text-align: center; color: var(--usx-color-on-surface-muted)">
          No routes match your search.
        </div>
        <div v-else class="registry-list">
          <div v-for="route in paginatedRoutes" :key="route.path + route.method" class="registry-route-row">
            <span class="usx-badge" :class="{
              'usx-badge--accent': route.method === 'GET',
              'usx-badge--success': route.method === 'POST',
              'usx-badge--error': route.method === 'DELETE'
            }" class="registry-badge--method">
              {{ route.method }}
            </span>
            <span style="font-family: var(--usx-font-family-mono); font-size: var(--usx-font-size-sm); flex: 1">
              {{ route.path }}
            </span>
            <span style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)">
              {{ route.handler }}
            </span>
          </div>
        </div>
        <div v-if="routePages > 1" class="usx-flex-center usx-mt-md usx-gap-sm">
          <button class="usx-btn--primary" :disabled="routePage === 1" @click="routePage--" style="min-height: var(--usx-touch-min-sm); padding: var(--usx-spacing-xs) var(--usx-spacing-sm)">
            <span class="material-symbols-outlined">chevron_left</span>
          </button>
          <span style="font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted)">Page {{ routePage }} of {{ routePages }}</span>
          <button class="usx-btn--primary" :disabled="routePage === routePages" @click="routePage++" style="min-height: var(--usx-touch-min-sm); padding: var(--usx-spacing-xs) var(--usx-spacing-sm)">
            <span class="material-symbols-outlined">chevron_right</span>
          </button>
        </div>
      </div>

      <!-- Runtimes View -->
      <div v-if="activeSubTab === 'runtimes'" class="registry-view">
        <h4>Runtimes ({{ filteredRuntimes.length }})</h4>
        <div v-if="Object.keys(filteredRuntimes).length === 0" class="usx-compact" style="text-align: center; color: var(--usx-color-on-surface-muted)">
          No runtimes match your search.
        </div>
        <div v-else class="registry-grid">
          <div v-for="(rt, name) in filteredRuntimes" :key="name" class="usx-card registry-card">
            <div class="usx-flex-between">
              <span style="font-weight: var(--usx-font-weight-semibold); font-family: var(--usx-font-family-mono)">
                {{ name }}
              </span>
            </div>
            <div style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)" class="usx-mt-sm">
              {{ rt.file }}
            </div>
            <div class="usx-flex-row usx-gap-xs usx-mt-sm" style="flex-wrap: wrap">
              <span v-if="rt.endpoints?.length" class="usx-badge usx-badge--accent registry-badge--compact">
                {{ rt.endpoints.length }} endpoints
              </span>
              <span v-if="rt.commands?.length" class="usx-badge registry-badge--compact">
                {{ rt.commands.length }} commands
              </span>
            </div>
            <div v-if="rt.endpoints?.length" class="usx-flex-row usx-gap-xs usx-mt-sm" style="flex-wrap: wrap">
              <span v-for="ep in rt.endpoints.slice(0, 6)" :key="ep" class="usx-badge registry-badge--compact registry-badge--mono">
                {{ ep }}
              </span>
              <span v-if="rt.endpoints.length > 6" style="font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted)">
                +{{ rt.endpoints.length - 6 }} more
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface SkillItem {
  skill_id: string
  name: string
  file: string
  category: string
  description: string
  params: { name: string; type: string; description: string }[]
  timeout: number
  requires_confirmation: boolean
}

interface PathItem {
  path: string
  type: string
  description: string
}

interface VariableItem {
  scope: string
  file?: string
  description: string
  examples?: string[]
}

interface SecretItem {
  key: string
  scope: string
  store?: string
  description: string
}

interface McpItem {
  name: string
  command: string
  cwd?: string
  file?: string
  disabled?: boolean
}

interface RouteItem {
  method: string
  path: string
  handler: string
}

interface RuntimeItem {
  file: string
  endpoints: string[]
  commands: string[]
  variables: Record<string, string>
}

// Hard-coded ecosystem data (from skill_ecosystem_audit would generate this)
const skills = ref<SkillItem[]>([])
const paths = ref<PathItem[]>([])
const variables = ref<VariableItem[]>([])
const secrets = ref<SecretItem[]>([])
const mcpServers = ref<McpItem[]>([])
const routes = ref<RouteItem[]>([])
const runtimes = ref<Record<string, RuntimeItem>>({})

const activeSubTab = ref('skills')
const searchQuery = ref('')
const repoFilter = ref('')
const routePage = ref(1)
const pageSize = 20

const repos = computed(() => ['uCore', 'uCode', 'HomeNest'])

const subTabs = computed(() => [
  { id: 'skills', label: 'Skills', icon: 'extension', count: filteredSkills.value.length },
  { id: 'paths', label: 'Paths', icon: 'folder', count: filteredPaths.value.length },
  { id: 'variables', label: 'Variables', icon: 'tune', count: filteredVariables.value.length },
  { id: 'secrets', label: 'Secrets', icon: 'key', count: filteredSecrets.value.length },
  { id: 'mcp', label: 'MCP', icon: 'dns', count: filteredMcp.value.length },
  { id: 'routes', label: 'Routes', icon: 'alt_route', count: filteredRoutes.value.length },
  { id: 'runtimes', label: 'Runtimes', icon: 'memory', count: filteredRuntimes.value.length },
])

const totalItems = computed(() =>
  skills.value.length + paths.value.length + variables.value.length +
  secrets.value.length + mcpServers.value.length + routes.value.length +
  Object.keys(runtimes.value).length
)

function matchSearch(item: any, fields: string[]): boolean {
  if (!searchQuery.value) return true
  const q = searchQuery.value.toLowerCase()
  for (const f of fields) {
    const val = (item[f] || '').toString().toLowerCase()
    if (val.includes(q)) return true
  }
  return false
}

const filteredSkills = computed(() =>
  skills.value.filter(s => matchSearch(s, ['name', 'skill_id', 'file', 'category', 'description']))
)
const filteredPaths = computed(() =>
  paths.value.filter(p => matchSearch(p, ['path', 'type', 'description']))
)
const filteredVariables = computed(() =>
  variables.value.filter(v => matchSearch(v, ['scope', 'description']))
)
const filteredSecrets = computed(() =>
  secrets.value.filter(s => matchSearch(s, ['key', 'scope', 'description', 'store']))
)
const filteredMcp = computed(() =>
  mcpServers.value.filter(m => matchSearch(m, ['name', 'command']))
)
const filteredRoutes = computed(() =>
  routes.value.filter(r => matchSearch(r, ['path', 'method', 'handler']))
)
const filteredRuntimes = computed(() => {
  const result: Record<string, RuntimeItem> = {}
  for (const [key, rt] of Object.entries(runtimes.value)) {
    if (!searchQuery.value || key.toLowerCase().includes(searchQuery.value.toLowerCase())) {
      result[key] = rt
    }
  }
  return result
})

const routePages = computed(() => Math.max(1, Math.ceil(filteredRoutes.value.length / pageSize)))
const paginatedRoutes = computed(() => {
  const start = (routePage.value - 1) * pageSize
  return filteredRoutes.value.slice(start, start + pageSize)
})

function loadRegistry() {
  try {
    const raw = localStorage.getItem('ucore-ecosystem-registry')
    if (raw) {
      const data = JSON.parse(raw)
      const eco = data.ecosystem || {}
      skills.value = eco.skills?.items || []
      paths.value = eco.paths?.items || []
      variables.value = eco.variables?.items || []
      secrets.value = eco.secrets?.items || []
      mcpServers.value = eco.mcp_servers?.items || []
      routes.value = eco.routes?.items || []
      runtimes.value = eco.runtimes?.items || {}
    }
  } catch {
    // Graceful — no registry data available
  }
}

onMounted(() => {
  loadRegistry()
})
</script>

<style scoped>
.registry-panel {
  display: flex;
  gap: 0;
  height: 100%;
  min-height: 500px;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  overflow: hidden;
}

/* ─── Left Sidebar ───────────────────────────────────────────── */
.registry-sidebar {
  width: 260px;
  min-width: 220px;
  flex-shrink: 0;
  background: var(--usx-color-surface-variant);
  border-right: var(--usx-border-width) solid var(--usx-color-border);
  display: flex;
  flex-direction: column;
  padding: var(--usx-spacing-md);
  gap: var(--usx-spacing-sm);
}

.registry-sidebar__title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0;
  padding: 0 var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
}

.registry-sidebar__tabs {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  overflow-y: auto;
}

.registry-sidebar__tab {
  display: flex;
  align-items: center;
  gap: var(--usx-icon-gap);
  padding: var(--usx-spacing-sm) var(--usx-spacing-sm);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  text-align: left;
  transition: all var(--usx-transition-fast);
  width: 100%;
}

.registry-sidebar__tab:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.registry-sidebar__tab--active {
  background: var(--usx-color-primary-disabled);
  color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-semibold);
}

.registry-sidebar__tab-label {
  flex: 1;
}

.registry-sidebar__tab-count {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  min-width: 24px;
  text-align: right;
}

.registry-sidebar__tab--active .registry-sidebar__tab-count {
  color: var(--usx-color-primary);
}

.registry-sidebar__summary {
  padding: var(--usx-spacing-sm);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
}

/* ─── Right Content Area ─────────────────────────────────────── */
.registry-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.registry-summary-cards {
  display: flex;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.registry-summary-card {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  cursor: pointer;
  transition: all var(--usx-transition-fast);
  min-width: 120px;
  flex: 1;
}

.registry-summary-card:hover {
  border-color: var(--usx-color-primary);
}

.registry-summary-card--active {
  border-color: var(--usx-color-primary);
  background: var(--usx-color-primary-disabled);
}

.registry-search {
  width: 100%;
  min-height: var(--usx-input-height-sm);
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  box-sizing: border-box;
}

.registry-view {
  flex: 1;
  overflow-y: auto;
}

.registry-grid {
  display: grid;
  gap: var(--usx-grid-gap-sm);
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

.registry-card {
  padding: var(--usx-spacing-md);
}

.registry-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.registry-route-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border-light);
}

.registry-badge--xs {
  font-size: var(--usx-font-size-xs);
}

.registry-badge--compact {
  padding: var(--usx-spacing-1) var(--usx-spacing-2);
  font-size: var(--usx-font-size-xs);
}

.registry-badge--mono {
  font-family: var(--usx-font-family-mono);
}

.registry-badge--method {
  min-width: 48px;
  text-align: center;
  font-size: var(--usx-font-size-xs);
  padding: var(--usx-spacing-1) var(--usx-spacing-2);
}
</style>