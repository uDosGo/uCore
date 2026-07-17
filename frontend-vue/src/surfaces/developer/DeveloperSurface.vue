<template>
  <div class="developer-surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="dev.activeTab"
      :tabs="DEVELOPER_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="developer-content-inner">
      <div class="developer-content">
        <ControlPanel v-if="dev.activeTab === 'control'" />
        <ModelsPanel v-else-if="dev.activeTab === 'models'" />
        <AgentsPanel v-else-if="dev.activeTab === 'agents'" />
        <KanbanPanel v-else-if="dev.activeTab === 'kanban'" />
        <ReposPanel v-else-if="dev.activeTab === 'repos'" />
        <ReviewPanel v-else-if="dev.activeTab === 'review'" />
        <SkillsPanel v-else-if="dev.activeTab === 'skills'" />
        <FeedPanel v-else-if="dev.activeTab === 'feed'" />
        <RegistryPanel v-else-if="dev.activeTab === 'registry'" />
        <WorkflowsPanel v-else-if="dev.activeTab === 'workflows'" />
        <MCPServersPanel v-else-if="dev.activeTab === 'mcp-servers'" />
        <DocLangPanel v-else-if="dev.activeTab === 'doclang'" />
        <SettingsPanel v-else-if="dev.activeTab === 'settings'" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component DeveloperSurface
 * @description Developer Lane — tabbed surface for models, agents, kanban, repos,
 * review, skills, workflows, MCP servers, and settings.
 * Ported from DeveloperSurface.tsx (React).
 * @category surfaces
 * @usage Routed at '/developer/*'
 */
import { defineAsyncComponent } from 'vue'
import { useShellStore } from '../../stores/shell'
import { useDeveloperStore, DEVELOPER_TABS } from '../../stores/developer'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

const shell = useShellStore()

// Eager: Control is the default tab
import ControlPanel from './panels/ControlPanel.vue'

// Lazy: load other panels only when their tab is selected
const ModelsPanel = defineAsyncComponent(() => import('./panels/ModelsPanel.vue'))
const AgentsPanel = defineAsyncComponent(() => import('./panels/AgentsPanel.vue'))
const KanbanPanel = defineAsyncComponent(() => import('./panels/KanbanPanel.vue'))
const ReposPanel = defineAsyncComponent(() => import('./panels/ReposPanel.vue'))
const ReviewPanel = defineAsyncComponent(() => import('./panels/ReviewPanel.vue'))
const SkillsPanel = defineAsyncComponent(() => import('./panels/SkillsPanel.vue'))
const FeedPanel = defineAsyncComponent(() => import('./panels/FeedPanel.vue'))
const RegistryPanel = defineAsyncComponent(() => import('./panels/RegistryPanel.vue'))
const WorkflowsPanel = defineAsyncComponent(() => import('./panels/WorkflowsPanel.vue'))
const MCPServersPanel = defineAsyncComponent(() => import('./panels/MCPServersPanel.vue'))
const DocLangPanel = defineAsyncComponent(() => import('./panels/DocLangPanel.vue'))
const SettingsPanel = defineAsyncComponent(() => import('./panels/SettingsPanel.vue'))

const dev = useDeveloperStore()
</script>

<style scoped>
.developer-surface {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.developer-tabs-inner {
  flex-shrink: 0;
}

.developer-tabs {
  display: flex;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  
  background: var(--usx-color-surface);
  overflow-x: auto;
}

.developer-tab {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  border-radius: var(--usx-radius-md);
  white-space: nowrap;
  transition: all 0.15s ease;
}

.developer-tab:hover {
  background: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

.developer-tab,
.developer-tab:hover,
.developer-tab--active {
  transition: background var(--usx-transition-fast), color var(--usx-transition-fast);
}

.developer-tab--active {
  background: var(--usx-color-background);
  color: var(--usx-color-primary);
}

.developer-content-inner {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--usx-spacing-xl);
  box-sizing: border-box;
}

.developer-content {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}
</style>
