<template>
  <div class="wf-panel">
    <div class="surface__panel">
      <h3 class="surface__panel-title">Publish</h3>
      <p class="surface__panel-description">Manage workflow definitions, run workflows, and view execution logs</p>
    </div>

    <div v-if="wf.loading" class="wf-loading">
      <UIcon name="sync" /> Loading workflows...
    </div>

    <!-- Workflow definitions -->
    <div class="wf-section">
      <h4 class="wf-section-title">Workflow Definitions</h4>
      <div class="wf-workflow-grid" v-if="wf.workflowDefinitions.length > 0">
        <div v-for="def in wf.workflowDefinitions" :key="def.id" class="wf-workflow-card">
          <div class="wf-workflow-card-header">
            <UIcon name="workflow" />
            <span class="wf-workflow-name">{{ def.name }}</span>
            <UBadge type="info" size="sm">{{ def.schedule }}</UBadge>
          </div>
          <p class="wf-workflow-desc">{{ def.description || 'No description' }}</p>
          <div class="wf-workflow-steps">
            <span class="wf-workflow-steps-label">{{ def.steps?.length || 0 }} steps:</span>
            <span v-for="(step, i) in def.steps" :key="i" class="wf-step-badge">
              <UIcon name="extension" />
              {{ step.skill_id }}
            </span>
          </div>
          <div class="wf-workflow-footer">
            <span class="wf-workflow-id">ID: {{ def.id }}</span>
            <button class="usx-button usx-btn--primary" @click="runWorkflow(def.id)">Run</button>
          </div>
        </div>
      </div>
      <div v-else-if="!wf.loading" class="wf-empty-small">
        No workflow definitions found. Create one via POST /api/workflows.
      </div>
    </div>

    <!-- Workflow runs history -->
    <div class="wf-section">
      <h4 class="wf-section-title">Recent Runs</h4>
      <div class="wf-run-history" v-if="wf.workflowRuns.length > 0">
        <div v-for="run in wf.workflowRuns.slice(0, 10)" :key="run.run_id" class="wf-run-card">
          <div class="wf-run-card-header">
            <UBadge
              :type="run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'warning'"
              size="sm"
            >
              {{ run.status }}
            </UBadge>
            <span class="wf-run-wf-name">{{ run.workflow_name || run.workflow_id }}</span>
            <span class="wf-run-id wf-monospace">{{ run.run_id }}</span>
          </div>
          <div class="wf-run-timing">
            <span>Started: {{ formatTime(run.started_at) }}</span>
            <span>Finished: {{ formatTime(run.finished_at) }}</span>
          </div>
          <div class="wf-run-steps" v-if="run.steps?.length">
            <span class="wf-run-steps-label">Steps:</span>
            <div v-for="step in run.steps" :key="step.index" class="wf-run-step-row">
              <UIcon
                :name="step.success ? 'check_circle' : 'error'"
                :size="12"
                :class="step.success ? 'wf-icon--success' : 'wf-icon--danger'"
              />
              <span class="wf-monospace">{{ step.skill_id }}</span>
              <span v-if="step.error" class="wf-step-error">{{ step.error }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="!wf.loading" class="wf-empty-small">No workflow runs yet.</div>
    </div>

    <!-- Create workflow form placeholder -->
    <details class="wf-create-form">
      <summary class="wf-create-summary">
        <UIcon name="add" /> Create New Workflow
      </summary>
      <div class="wf-create-body">
        <p class="wf-muted">
          POST to <code>/api/workflows</code> with <code>{ name, steps: [{ type: "skill", skill_id: "..." }] }</code>
        </p>
        <p class="wf-muted">
          Workflows are defined as a sequence of skill executions run in order.
          Each step references a registered skill by ID.
        </p>
      </div>
    </details>
  </div>
</template>

<script setup lang="ts">
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import { useWorkflowStore } from '../../../stores/workflow'

const wf = useWorkflowStore()

function formatTime(iso: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

const API = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

async function runWorkflow(workflowId: string): Promise<void> {
  try {
    const res = await fetch(`${API}/api/workflows/${workflowId}/run`, {
      method: 'POST',
      signal: AbortSignal.timeout(60000),
    })
    if (res.ok) {
      // Refresh runs after running
      await wf.fetchWorkflowRuns()
    }
  } catch (e: any) {
    console.warn('Failed to run workflow:', e)
  }
}
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
}

.wf-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.wf-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-section-title {
  margin: 0;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.wf-workflow-grid {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-workflow-card {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
}

.wf-workflow-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-xs);
}

.wf-workflow-name {
  font-weight: var(--usx-font-weight-semibold);
  flex: 1;
  font-size: var(--usx-font-size-sm);
}

.wf-workflow-desc {
  margin: 0 0 var(--usx-spacing-sm) 0;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.wf-workflow-steps {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
  margin-bottom: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xs);
}

.wf-workflow-steps-label {
  color: var(--usx-color-on-surface-muted);
}

.wf-step-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-badge-padding-vertical) var(--usx-badge-padding-horizontal);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-sm);
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
}

.wf-workflow-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wf-workflow-id {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.wf-run-history {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-run-card {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-md);
  border-left: 3px solid var(--usx-color-primary);
}

.wf-run-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
}

.wf-run-wf-name {
  flex: 1;
  font-weight: var(--usx-font-weight-medium);
}

.wf-run-id {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.wf-run-timing {
  display: flex;
  gap: var(--usx-spacing-lg);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  margin-bottom: var(--usx-spacing-sm);
  font-family: var(--usx-font-family-mono);
}

.wf-run-steps {
  font-size: var(--usx-font-size-xs);
}

.wf-run-steps-label {
  color: var(--usx-color-on-surface-muted);
  display: block;
  margin-bottom: var(--usx-spacing-xs);
}

.wf-run-step-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) 0;
}

.wf-step-error {
  color: var(--usx-color-danger);
  font-style: italic;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wf-monospace {
  font-family: var(--usx-font-family-mono);
}

.wf-muted {
  color: var(--usx-color-on-surface-muted);
}

.wf-empty-small {
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  text-align: center;
  font-style: italic;
}

.wf-create-form {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-md);
}

.wf-create-summary {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-primary);
}

.wf-create-body {
  margin-top: var(--usx-spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.wf-create-body code {
  padding: var(--usx-spacing-xs) var(--usx-spacing-xs);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-xs);
}

.wf-icon--success { color: var(--usx-color-success); }
.wf-icon--danger { color: var(--usx-color-danger); }
</style>