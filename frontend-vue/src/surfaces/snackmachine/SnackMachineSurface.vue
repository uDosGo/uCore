<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="sm.activeTab"
      :tabs="SNACKMACHINE_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />

    <div class="surface__content">
      <!-- Snacks Queue -->
      <div v-if="sm.activeTab === 'snacks'">
        <div class="usx-flex-between usx-mb-md">
          <h3 class="surface__panel-title" style="margin:0">Snack Queue</h3>
          <UButton variant="secondary" size="sm" icon="refresh">Refresh</UButton>
        </div>
        <div class="sm-snacks-list">
          <div v-for="snack in sm.snacks" :key="snack.id" class="sm-snack-row">
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
          <UButton variant="primary" size="sm" icon="add">New Workflow</UButton>
        </div>
        <div class="sm-workflows-list">
          <div v-for="wf in workflows" :key="wf.id" class="surface__panel">
            <div class="usx-flex-row">
              <UIcon name="account_tree" />
              <span style="font-weight:600;flex:1">{{ wf.name }}</span>
              <UBadge :type="wf.enabled ? 'success' : 'info'" size="sm">{{ wf.enabled ? 'enabled' : 'disabled' }}</UBadge>
            </div>
            <p style="font-size:var(--usx-font-size-sm);color:var(--pico-muted-color);margin:var(--usx-spacing-xs) 0">{{ wf.description }}</p>
            <div class="usx-flex-row usx-gap-md" style="font-size:var(--usx-font-size-sm);color:var(--pico-muted-color)">
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
            <div class="usx-flex-row usx-gap-md" style="font-size:var(--usx-font-size-sm);color:var(--pico-muted-color);margin:var(--usx-spacing-xs) 0">
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
        <p class="usx-mb-md" style="font-size:var(--usx-font-size-sm);color:var(--pico-muted-color)">Bidirectional sync between AppFlowy and local vault.</p>
        <div class="usx-flex-row usx-gap-sm">
          <UButton variant="primary" icon="sync">Sync Now</UButton>
          <UButton variant="secondary" icon="history">View Log</UButton>
        </div>
      </div>

      <!-- Variables -->
      <div v-else-if="sm.activeTab === 'variables'">
        <h3 class="surface__panel-title">Variables</h3>
        <div class="sm-vars-list">
          <div v-for="v in variables" :key="v.key" class="sm-var-row">
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
          <div v-for="entry in schedule" :key="entry.id" class="sm-schedule-row">
            <UIcon name="schedule" />
            <span class="sm-schedule-name">{{ entry.workflow_name }}</span>
            <code class="sm-schedule-cron">{{ entry.cron }}</code>
            <span class="sm-schedule-next">{{ entry.next_run }}</span>
            <UBadge :type="entry.enabled ? 'success' : 'info'" size="sm">{{ entry.enabled ? 'on' : 'off' }}</UBadge>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'
import UButton from '../../skills/atoms/UButton.vue'
import { useShellStore } from '../../stores/shell'
import { useSnackMachineStore, SNACKMACHINE_TABS } from '../../stores/snackmachine'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

const shell = useShellStore()
const sm = useSnackMachineStore()

const workflows = [
  { id: 'wf1', name: 'Daily Docs Sync', description: 'Sync documentation to vault', schedule: '0 6 * * *', enabled: true, steps: [{ skill_id: 'vault_sync', params: {} }, { skill_id: 'git_commit', params: {} }] },
  { id: 'wf2', name: 'Git Maintenance', description: 'Check and repair git state', schedule: '0 */12 * * *', enabled: true, steps: [{ skill_id: 'git_maintenance', params: {} }] },
  { id: 'wf3', name: 'Brain Sync', description: 'Synthesize project changes', schedule: '0 0 * * 0', enabled: false, steps: [{ skill_id: 'brain_sync', params: {} }] },
]

const variables = [
  { key: 'SNACKBAR_API', value: 'http://localhost:8484', scope: 'system' },
  { key: 'UCORE_API', value: 'http://localhost:8000', scope: 'system' },
  { key: 'VITE_DEV_MODE', value: 'true', scope: 'global' },
]

const schedule = [
  { id: 's1', workflow_id: 'wf1', workflow_name: 'Daily Docs Sync', cron: '0 6 * * *', next_run: 'Tomorrow 06:00', enabled: true },
  { id: 's2', workflow_id: 'wf2', workflow_name: 'Git Maintenance', cron: '0 */12 * * *', next_run: 'In 6 hours', enabled: true },
  { id: 's3', workflow_id: 'wf3', workflow_name: 'Brain Sync', cron: '0 0 * * 0', next_run: 'In 2 days', enabled: false },
]
</script>

<style scoped>
/* Surface-specific overrides only — layout handled by .surface__* classes */

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
  background: var(--pico-background-color);
  border-radius: var(--usx-border-radius-md);
}

.sm-snack-type {
  font-size: var(--usx-font-size-sm);
  font-weight: 500;
  min-width: 100px;
}

.sm-snack-source {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
}

.sm-snack-time {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  margin-left: auto;
}

.sm-workflows-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.sm-mcp-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

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
  border-radius: var(--usx-border-radius-sm);
}

.sm-var-row code {
  font-family: monospace;
  font-size: var(--usx-font-size-sm);
  color: var(--pico-primary);
  min-width: 160px;
}

.sm-var-row span {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  flex: 1;
}

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
  background: var(--pico-background-color);
  border-radius: var(--usx-border-radius-md);
}

.sm-schedule-name {
  font-size: var(--usx-font-size-sm);
  font-weight: 500;
  min-width: 140px;
}

.sm-schedule-cron {
  font-family: monospace;
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
}

.sm-schedule-next {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  margin-left: auto;
}
</style>
