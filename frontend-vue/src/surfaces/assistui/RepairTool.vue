<template>
  <div class="surface-repair-tool">
    <h3>Surface Repair Tool</h3>
    
    <div class="repair-section">
      <h4>1. Topbar Issues</h4>
      <button @click="repairTopbar" class="repair-btn">
        Fix Topbar Spacing
      </button>
      <div v-if="topbarFixed" class="repair-success">✓ Topbar spacing fixed</div>
    </div>
    
    <div class="repair-section">
      <h4>2. Sidebar Issues</h4>
      <button @click="repairSidebar" class="repair-btn">
        Fix Sidebar Visibility
      </button>
      <div v-if="sidebarFixed" class="repair-success">✓ Sidebar visibility fixed</div>
    </div>
    
    <div class="repair-section">
      <h4>3. Dashboard Cards</h4>
      <button @click="repairDashboard" class="repair-btn">
        Show Dashboard Cards
      </button>
      <div v-if="dashboardFixed" class="repair-success">✓ Dashboard cards visible</div>
    </div>
    
    <div class="repair-section">
      <h4>4. Spacing Reset</h4>
      <button @click="resetSpacing" class="repair-btn">
        Reset All Spacing
      </button>
      <div v-if="spacingReset" class="repair-success">✓ Spacing reset complete</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const topbarFixed = ref(false)
const sidebarFixed = ref(false)
const dashboardFixed = ref(false)
const spacingReset = ref(false)

const repairTopbar = () => {
  const topbar = document.querySelector('.assistui-topbar, .global-toolbar') as HTMLElement
  if (topbar) {
    topbar.style.minHeight = 'var(--usx-touch-min)'
    topbar.style.display = 'flex'
    topbarFixed.value = true
  }
}

const repairSidebar = () => {
  const sidebar = document.querySelector('.vault-sidebar, .assistui-conv-sidebar') as HTMLElement
  if (sidebar) {
    sidebar.style.display = 'block'
    sidebar.style.visibility = 'visible'
    sidebar.style.width = 'var(--usx-sidebar-width)'
    sidebarFixed.value = true
  }
}

const repairDashboard = () => {
  const dashboardGrid = document.querySelector('.dashboard-surface__grid') as HTMLElement
  if (dashboardGrid) {
    dashboardGrid.style.display = 'grid'
    dashboardGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(20ch, 1fr))'
    dashboardGrid.style.gap = 'var(--usx-spacing-md)'
    dashboardFixed.value = true
  }
}

const resetSpacing = () => {
  const body = document.querySelector('.usx-surface-body, .assistui-body, .developer-content') as HTMLElement
  if (body) {
    body.style.display = 'flex'
    body.style.flexDirection = 'column'
    body.style.gap = 'var(--usx-spacing-sm)'
    body.style.padding = 'var(--usx-spacing-md)'
    spacingReset.value = true
  }
}
</script>

<style scoped>
.surface-repair-tool {
  position: fixed;
  bottom: var(--usx-spacing-lg);
  left: var(--usx-spacing-lg);
  z-index: 10000;
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  border-radius: var(--usx-radius-lg);
  padding: var(--usx-spacing-lg);
  font-size: var(--usx-font-size-base);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.repair-section {
  margin-bottom: var(--usx-spacing-md);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-sm);
}

.repair-btn {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border: none;
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg);
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  margin: var(--usx-spacing-xs);
}

.repair-btn:hover {
  background: var(--usx-color-primary-hover);
}

.repair-success {
  color: var(--usx-color-success);
  font-size: var(--usx-font-size-sm);
  margin-top: var(--usx-spacing-xs);
}
</style>