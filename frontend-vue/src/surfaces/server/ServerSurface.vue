<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="srv.activeTab"
      :tabs="SERVER_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content">
      <!-- Dashboard -->
      <ServerDashboardPanel v-if="srv.activeTab === 'dashboard'" />

      <!-- Services -->
      <ServerServicesPanel v-else-if="srv.activeTab === 'services'" />
      <!-- Logs -->
      <ServerLogsPanel v-else-if="srv.activeTab === 'logs'" />
      <!-- Models -->
      <ServerModelsPanel v-else-if="srv.activeTab === 'models'" />
      <!-- Agents -->
      <ServerAgentsPanel v-else-if="srv.activeTab === 'agents'" />
      <!-- Budget -->
      <ServerBudgetPanel v-else-if="srv.activeTab === 'budget'" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component ServerSurface
 * @description Server operations surface — wired to /api/server/* backend.
 * Dashboard, services, logs, models, runtime agents, budget.
 * @category surfaces
 * @usage Routed at '/server/*'
 */
import { onMounted } from 'vue'
import { useShellStore } from '../../stores/shell'
import ServerDashboardPanel from './panels/ServerDashboardPanel.vue'
import ServerServicesPanel from './panels/ServerServicesPanel.vue'
import ServerLogsPanel from './panels/ServerLogsPanel.vue'
import ServerModelsPanel from './panels/ServerModelsPanel.vue'
import ServerAgentsPanel from './panels/ServerAgentsPanel.vue'
import ServerBudgetPanel from './panels/ServerBudgetPanel.vue'
import { useServerStore, SERVER_TABS } from '../../stores/server'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

const shell = useShellStore()
const srv = useServerStore()

onMounted(() => { srv.fetchAll() })
</script>

<style></style>
