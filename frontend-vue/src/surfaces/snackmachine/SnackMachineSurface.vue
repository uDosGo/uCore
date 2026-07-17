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
              <h3 class="surface__panel-title sm-panel-heading">Snack Queue</h3>
              <div class="usx-flex-row usx-gap-sm">
                <UButton variant="secondary" size="sm" icon="add" @click="sm.seedDefaultSnacks">Seed Defaults</UButton>
                <UButton variant="secondary" size="sm" icon="refresh" @click="sm.fetchSnacks">Refresh</UButton>
              </div>
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
            <div v-if="sm.systemSnacks.length > 0" class="sm-system-snacks">
              <h4 class="surface__panel-title sm-section-heading">Default System Snacks</h4>
              <div class="sm-system-snacks-list">
                <div v-for="snack in sm.systemSnacks" :key="snack.id" class="sm-system-snack-row">
                  <span class="sm-system-snack-name">{{ snack.name }}</span>
                  <UBadge type="info" size="sm">{{ snack.kind }}</UBadge>
                </div>
              </div>
            </div>
          </div>

          <!-- Workflows -->
          <div v-else-if="sm.activeTab === 'workflows'">
            <div class="usx-flex-between usx-mb-md">
              <h3 class="surface__panel-title sm-panel-heading">Workflows</h3>
              <UButton variant="primary" size="sm" icon="add" @click="createWorkflow">New Workflow</UButton>
            </div>
            <div class="sm-workflows-list">
              <div v-for="wf in sm.workflows" :key="wf.id" class="surface__panel">
                <div class="usx-flex-row">
                  <UIcon name="account_tree" />
                  <span class="sm-row-title">{{ wf.name }}</span>
                  <UBadge :type="wf.enabled ? 'success' : 'info'" size="sm">{{ wf.enabled ? 'enabled' : 'disabled' }}</UBadge>
                </div>
                <p class="sm-row-description">{{ wf.description }}</p>
                <div class="usx-flex-row usx-gap-md sm-row-meta">
                  <span>{{ wf.schedule }}</span>
                  <span>{{ wf.steps.length }} steps</span>
                </div>
              </div>
            </div>
          </div>

          <!-- MCP Bridge -->
          <div v-else-if="sm.activeTab === 'mcp'">
            <h3 class="surface__panel-title sm-panel-heading">MCP Bridge</h3>
            <div class="sm-mcp-list">
              <div v-for="server in sm.mcpServers" :key="server.id" class="surface__panel">
                <div class="usx-flex-row">
                  <UIcon name="dns" />
                  <span class="sm-row-title">{{ server.name }}</span>
                  <UBadge :type="server.status === 'online' ? 'success' : 'error'" size="sm">{{ server.status }}</UBadge>
                </div>
                <div class="usx-flex-row usx-gap-md sm-row-meta sm-row-meta--spaced">
                  <span>{{ server.transport }}</span>
                  <span>{{ server.tools.length }} tools</span>
                </div>
                <div class="usx-flex-row usx-gap-xs sm-wrap">
                  <UBadge v-for="tool in server.tools" :key="tool" type="info" size="sm">{{ tool }}</UBadge>
                </div>
              </div>
            </div>
          </div>

          <!-- Vault Sync -->
          <div v-else-if="sm.activeTab === 'vault'">
            <h3 class="surface__panel-title sm-panel-heading">Vault Sync</h3>
            <p class="sm-muted-text sm-muted-text--spaced">Mirror local vault layers to AppFlowy workspaces.</p>
            <div class="usx-flex-row usx-gap-sm usx-mb-md">
              <UButton variant="primary" icon="sync" :disabled="sm.syncingVault" @click="syncVault('User Vault')">
                {{ sm.syncingVault ? 'Syncing…' : 'Sync User Vault' }}
              </UButton>
              <UButton variant="secondary" icon="sync_alt" :disabled="sm.syncingVault" @click="syncVault('Shared Vault')">Sync Shared</UButton>
              <UButton variant="secondary" icon="history" @click="sm.fetchVaultSyncStatus">Refresh Status</UButton>
            </div>
            <div class="surface__panel">
              <h4 class="surface__panel-title sm-section-heading">Mirror Status</h4>
              <p class="sm-status" v-if="!sm.latestImportJob">No sync job recorded yet.</p>
              <div v-else class="sm-sync-job">
                <div class="sm-sync-job-row">
                  <span>Job</span>
                  <code>{{ sm.latestImportJob.id }}</code>
                </div>
                <div class="sm-sync-job-row">
                  <span>Status</span>
                  <UBadge :type="syncBadgeType(sm.latestImportJob.status)" size="sm">{{ sm.latestImportJob.status }}</UBadge>
                </div>
                <div class="sm-sync-job-row">
                  <span>Progress</span>
                  <span>{{ sm.latestImportJob.progress }}%</span>
                </div>
                <div class="sm-sync-job-row">
                  <span>Message</span>
                  <span>{{ sm.latestImportJob.message || '—' }}</span>
                </div>
              </div>
            </div>
            <div class="surface__panel usx-mt-md" v-if="sm.indexCoverage">
              <h4 class="surface__panel-title sm-section-heading">Index Coverage</h4>
              <p class="sm-status sm-status--compact">
                {{ sm.indexCoverage.total_docs }} indexed docs · {{ sm.indexCoverage.coverage_pct.toFixed(1) }}% coverage
              </p>
            </div>
          </div>

          <!-- Variables -->
          <div v-else-if="sm.activeTab === 'variables'">
            <h3 class="surface__panel-title sm-panel-heading">Variables</h3>
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
            <h3 class="surface__panel-title sm-panel-heading">Scheduler</h3>
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
            <h4 class="surface__panel-title sm-section-heading">Backend Status</h4>
            <div class="usx-flex-row usx-gap-sm">
              <UBadge :type="sm.backendOk ? 'success' : 'error'" size="sm">
                {{ sm.backendOk ? 'connected' : 'disconnected' }}
              </UBadge>
              <span class="sm-muted-text">
                {{ sm.backendOk ? API_BASE : 'unreachable' }}
              </span>
            </div>
            <div class="usx-mt-sm">
              <UButton variant="secondary" size="sm" icon="refresh" @click="sm.fetchAll">
                Refresh All
              </UButton>
            </div>
          </div>

          <div class="surface__panel usx-mt-md">
            <h4 class="surface__panel-title sm-section-heading">Quick Info</h4>
            <p class="sm-muted-text sm-muted-text--compact">
              {{ sm.snacks.length }} snack(s) in queue
            </p>
            <p class="sm-muted-text sm-muted-text--stacked">
              {{ sm.systemSnacks.length }} system snack(s) available
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
import { onMounted, onUnmounted, watch } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'
import UButton from '../../skills/atoms/UButton.vue'
import { useShellStore } from '../../stores/shell'
import { useSnackMachineStore, SNACKMACHINE_TABS } from '../../stores/snackmachine'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

const shell = useShellStore()
const sm = useSnackMachineStore()
let syncPollTimer: ReturnType<typeof setInterval> | null = null

function clearSyncPoller() {
  if (!syncPollTimer) return
  clearInterval(syncPollTimer)
  syncPollTimer = null
}

function ensureSyncPoller() {
  if (syncPollTimer) return
  syncPollTimer = setInterval(() => {
    void sm.fetchVaultSyncStatus()
  }, 3000)
}

async function syncVault(source: string) {
  try {
    await sm.syncVault(source)
    await sm.fetchAll()
  } catch (e: any) { console.warn('Vault sync failed:', e.message) }
}

function syncBadgeType(status: string): 'success' | 'warning' | 'error' | 'info' {
  if (status === 'completed') return 'success'
  if (status === 'in-progress' || status === 'queued') return 'warning'
  if (status === 'error' || status === 'failed') return 'error'
  return 'info'
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

onMounted(() => {
  void sm.fetchAll()
})

watch(
  () => sm.latestImportJob?.status,
  (status) => {
    if (status === 'queued' || status === 'in-progress') {
      ensureSyncPoller()
      return
    }
    clearSyncPoller()
  },
  { immediate: true },
)

onUnmounted(() => {
  clearSyncPoller()
})
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

.sm-panel-heading,
.sm-section-heading {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0;
}

.sm-section-heading {
  margin-bottom: var(--usx-spacing-sm);
}

.sm-muted-text {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.sm-muted-text--spaced {
  margin-bottom: var(--usx-spacing-md);
}

.sm-muted-text--compact {
  margin: 0;
}

.sm-muted-text--stacked {
  margin: var(--usx-spacing-xs) 0 0 0;
}

.sm-row-title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  flex: 1;
  min-width: 0;
}

.sm-row-description {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin: var(--usx-spacing-xs) 0;
}

.sm-row-meta {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.sm-row-meta--spaced {
  margin: var(--usx-spacing-xs) 0;
}

.sm-wrap {
  flex-wrap: wrap;
}

/* ─── Sidebar Column ─── */

.sm-sidebar {
  flex-shrink: 0;
  width: clamp(240px, 24vw, 320px);
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

.sm-status--compact {
  margin-bottom: 0;
}

.sm-status--error {
  color: var(--usx-color-danger);
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
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-medium);
  min-width: 8ch;
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

.sm-system-snacks {
  margin-top: var(--usx-spacing-lg);
}

.sm-system-snacks-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.sm-system-snack-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
}

.sm-system-snack-name {
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface);
}

.sm-sync-job {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.sm-sync-job-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
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
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-primary);
  min-width: 12ch;
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
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-medium);
  min-width: 10ch;
}

.sm-schedule-cron {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.sm-schedule-next {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-left: auto;
}
</style>