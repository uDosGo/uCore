<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="sm.activeTab"
      :tabs="SNACKMACHINE_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <!-- Content area -->
    <div class="surface__content">
      <div class="sm-layout">

        <!-- Left/Main panel: the active tab content -->
        <div class="sm-panel">
          <!-- Snacks Queue -->
          <div v-if="sm.activeTab === 'snacks'">
            <div class="usx-flex-between usx-mb-md">
              <h3 class="surface__panel-title" style="margin:0">Snack Queue</h3>
              <UButton variant="secondary" size="sm" icon="refresh" @click="sm.fetchSnacks">Refresh</UButton>
            </div>
            <p v-if="sm.loading" class="sm-status">Loading…</p>
            <p v-else-if="sm.error" class="sm-status sm-status--error">Error: {{ sm.error }}</p>
            <p v-else-if="sm.snacks.length === 0" class="sm-status">No snacks running.</p>
            <div v-else class="sm-snacks-list">
              <div v-for="snack in sm.snacks" :key="snack.id" class="surface__panel sm-snack-row">
                <UIcon :name="snack.type === 'clipboard' ? 'content_paste' : snack.type === 'workflow' ? 'account_tree' : 'build'" />
                <span class="sm-snack-type">{{ snack.type }}</span>
                <span class="sm-snack-source">{{ snack.source }}</span>
                <span class="sm-snack-time">{{ snack.timestamp }}</span>
                <UBadge :type="snack.status === 'active' ? 'success' : snack.status === 'queued' ? 'warning' : 'info'" size="sm">{{ snack.status }}</UBadge>
              </div>
            </div>
          </div>

          <!-- Workflows -->
          <div v-else-if="sm.activeTab === 'workflows'">
            <div class="usx-flex-between usx-mb-md">
              <h3 class="surface__panel-title" style="margin:0">Workflows</h3>
              <UButton variant="primary" size="sm" icon="add" @click="createWorkflow">New Workflow</UButton>
            </div>
            <div class="sm-workflows-list">
              <div v-for="wf in sm.workflows" :key="wf.id" class="surface__panel">
                <div class="usx-flex-row">
                  <UIcon name="account_tree" />
                  <span style="font-weight:600;flex:1">{{ wf.name }}</span>
                  <UBadge :type="wf.enabled ? 'success' : 'info'" size="sm">{{ wf.enabled ? 'enabled' : 'disabled' }}</UBadge>
                </div>
                <p style="font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted);margin:var(--usx-spacing-xs) 0">{{ wf.description }}</p>
                <div class="usx-flex-row usx-gap-md" style="font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted)">
                  <span>{{ wf.schedule }}</span>
                  <span>{{ wf.steps.length }} steps</span>
                </div>
              </div>
            </div>
          </div>

          <!-- MCP Bridge -->
          <div v-else-if="sm.activeTab === 'mcp'">
            <h3 class="surface__panel-title">MCP Bridge</h3>
            <div class="sm-mcp-list">
              <div v-for="server in sm.mcpServers" :key="server.id" class="surface__panel">
                <div class="usx-flex-row">
                  <UIcon name="dns" />
                  <span style="font-weight:600;flex:1">{{ server.name }}</span>
                  <UBadge :type="server.status === 'online' ? 'success' : 'error'" size="sm">{{ server.status }}</UBadge>
                </div>
                <div class="usx-flex-row usx-gap-md" style="font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted);margin:var(--usx-spacing-xs) 0">
                  <span>{{ server.transport }}</span>
                  <span>{{ server.tools.length }} tools</span>
                </div>
                <div class="usx-flex-row usx-gap-xs" style="flex-wrap:wrap">
                  <UBadge v-for="tool in server.tools" :key="tool" type="info" size="sm">{{ tool }}</UBadge>
                </div>
              </div>
            </div>
          </div>

          <!-- Vault Sync -->
          <div v-else-if="sm.activeTab === 'vault'">
            <h3 class="surface__panel-title">Vault Sync</h3>
            <p class="usx-mb-md" style="font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted)">Bidirectional sync between AppFlowy and local vault.</p>
            <div class="usx-flex-row usx-gap-sm">
              <UButton variant="primary" icon="sync" @click="syncVault">Sync Now</UButton>
              <UButton variant="secondary" icon="history" @click="sm.fetchVariables">View Log</UButton>
            </div>
          </div>

          <!-- Variables -->
          <div v-else-if="sm.activeTab === 'variables'">
            <h3 class="surface__panel-title">Variables</h3>
            <div class="sm-vars-list">
              <div v-for="v in sm.variables" :key="v.key" class="sm-var-row">
                <code>{{ v.key }}</code>
                <span>{{ v.value }}</span>
                <UBadge type="info" size="sm">{{ v.scope }}</UBadge>
              </div>
            </div>
          </div>

          <!-- Scheduler -->
          <div v-else-if="sm.activeTab === 'scheduler'">
            <h3 class="surface__panel-title">Scheduler</h3>
            <div class="sm-schedule-list">
              <div v-for="entry in sm.schedule" :key="entry.id" class="sm-schedule-row">
                <UIcon name="schedule" />
                <span class="sm-schedule-name">{{ entry.workflow_name }}</span>
                <code class="sm-schedule-cron">{{ entry.cron }}</code>
                <span class="sm-schedule-next">{{ entry.next_run }}</span>
                <UBadge :type="entry.enabled ? 'success' : 'info'" size="sm">{{ entry.enabled ? 'on' : 'off' }}</UBadge>
              </div>
            </div>
          </div>
        </div>

        <!-- Right column: live backend status -->
        <div class="sm-sidebar">
          <div class="surface__panel">
            <h4 class="surface__panel-title" style="margin-top:0">Backend Status</h4>
            <div class="usx-flex-row usx-gap-sm">
              <UBadge :type="sm.backendOk ? 'success' : 'error'" size="sm">
                {{ sm.backendOk ? 'connected' : 'disconnected' }}
              </UBadge>
              <span style="font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted)">
                {{ sm.backendOk ? 'http://localhost:5175' : 'unreachable' }}
              </span>
            </div>
            <div class="usx-mt-sm">
              <UButton variant="secondary" size="sm" icon="refresh" @click="sm.fetchAll">
                Refresh All
              </UButton>
            </div>
          </div>

          <div class="surface__panel usx-mt-md">
            <h4 class="surface__panel-title" style="margin-top:0">Quick Info</h4>
            <p style="font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted);margin:0">
              {{ sm.snacks.length }} snack(s) in queue
            </p>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component SnackMachineSurface
 * @description SnackMachine surface with tabbed navigation, snack queue, workflows,
 * MCP bridge, vault sync, variables, and scheduler.
 * Uses USX canonical .surface / SurfaceTabNav / .surface__content / column layout.
 * Data sourced from Pinia store (wired to backend endpoints).
 * @category surfaces
 * @usage Routed at '/snackmachine?tab=snacks'
 */
import { onMounted } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'
import UButton from '../../skills/atoms/UButton.vue'
import { useShellStore } from '../../stores/shell'
import { useSnackMachineStore, SNACKMACHINE_TABS } from '../../stores/snackmachine'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

const shell = useShellStore()
const sm = useSnackMachineStore()

async function syncVault() {
  try {
    await fetch(`${API_BASE}/api/skills/vault_sync/run`, { method: 'POST', signal: AbortSignal.timeout(30000) })
    await sm.fetchAll()
  } catch (e: any) { console.warn('Vault sync failed:', e.message) }
}

function createWorkflow() {
  const name = prompt('Workflow name:')
  if (!name) return
  // POST to create workflow then refresh
  fetch(`${API_BASE}/api/workflows`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, steps: [] }),
    signal: AbortSignal.timeout(10000),
  }).then(() => sm.fetchWorkflows()).catch(e => console.warn('Create workflow failed:', e.message))
}

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

onMounted(() => { sm.fetchAll() })
</script>

<style scoped>
/* ─── Layout — matches WorkflowSurface pattern ─── */

.sm-layout {
  display: flex;
  flex-direction: row;
  height: 100%;
  gap: var(--usx-spacing-md);
}

/* ─── Main Panel ─── */

.sm-panel {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* ─── Sidebar Column ─── */

.sm-sidebar {
  flex-shrink: 0;
  width: 280px;
  min-width: 240px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

/* ─── Status ─── */

.sm-status {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-bottom: var(--usx-spacing-md);
}

.sm-status--error {
  color: var(--usx-color-error, #c00);
}

/* ─── Snacks list ─── */

.sm-snacks-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.sm-snack-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
}

.sm-snack-type {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  min-width: 100px;
}

.sm-snack-source {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.sm-snack-time {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-left: auto;
}

/* ─── Workflows list ─── */

.sm-workflows-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

/* ─── MCP list ─── */

.sm-mcp-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

/* ─── Variables list ─── */

.sm-vars-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.sm-var-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
}

.sm-var-row code {
  font-family: monospace;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-primary);
  min-width: 160px;
}

.sm-var-row span {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  flex: 1;
}

/* ─── Schedule list ─── */

.sm-schedule-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.sm-schedule-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-background);
  border-radius: var(--usx-radius-md);
}

.sm-schedule-name {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  min-width: 140px;
}

.sm-schedule-cron {
  font-family: monospace;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.sm-schedule-next {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-left: auto;
}
</style>