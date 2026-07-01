<template>
  <div class="developer-surface">
    <div class="developer-content-inner">
      <div class="developer-content">
        <ModelsPanel v-if="dev.activeTab === 'models'" />
        <AgentsPanel v-else-if="dev.activeTab === 'agents'" />
        <KanbanPanel v-else-if="dev.activeTab === 'kanban'" />
        <ReposPanel v-else-if="dev.activeTab === 'repos'" />
        <ReviewPanel v-else-if="dev.activeTab === 'review'" />
        <SkillsPanel v-else-if="dev.activeTab === 'skills'" />
        <FeedPanel v-else-if="dev.activeTab === 'feed'" />
        <RegistryPanel v-else-if="dev.activeTab === 'registry'" />
        <WorkflowsPanel v-else-if="dev.activeTab === 'workflows'" />
        <MCPServersPanel v-else-if="dev.activeTab === 'mcp-servers'" />
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
import UIcon from '../../skills/atoms/UIcon.vue'
import { useDeveloperStore, DEVELOPER_TABS } from '../../stores/developer'
import ModelsPanel from './panels/ModelsPanel.vue'
import AgentsPanel from './panels/AgentsPanel.vue'
import KanbanPanel from './panels/KanbanPanel.vue'
import ReposPanel from './panels/ReposPanel.vue'
import ReviewPanel from './panels/ReviewPanel.vue'
import SkillsPanel from './panels/SkillsPanel.vue'
import FeedPanel from './panels/FeedPanel.vue'
import RegistryPanel from './panels/RegistryPanel.vue'
import WorkflowsPanel from './panels/WorkflowsPanel.vue'
import MCPServersPanel from './panels/MCPServersPanel.vue'
import SettingsPanel from './panels/SettingsPanel.vue'

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
  
  background: var(--pico-card-background-color, #161b22);
  overflow-x: auto;
}

.developer-tab {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: none;
  background: transparent;
  color: var(--pico-muted-color, #8b949e);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  font-weight: 500;
  border-radius: var(--usx-border-radius-md);
  white-space: nowrap;
  transition: all 0.15s ease;
}

.developer-tab:hover {
  background: var(--pico-border-color, #30363d);
  color: var(--pico-color, #c9d1d9);
}

.developer-tab--active {
  background: var(--pico-background-color);
  color: var(--pico-primary, #58a6ff);
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
