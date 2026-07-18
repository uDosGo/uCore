<template>
  <div class="diagnostic-panel">
    <h3>UI Diagnostics</h3>
    
    <!-- Topbar Status -->
    <div class="diagnostic-item">
      <span>Topbar Visible:</span>
      <span :class="{ 'status-ok': topbarVisible, 'status-error': !topbarVisible }">
        {{ topbarVisible ? '✓' : '✗' }}
      </span>
    </div>
    
    <!-- Sidebar Status -->
    <div class="diagnostic-item">
      <span>Sidebar Visible:</span>
      <span :class="{ 'status-ok': sidebarVisible, 'status-error': !sidebarVisible }">
        {{ sidebarVisible ? '✓' : '✗' }}
      </span>
    </div>
    
    <!-- Dashboard Cards Status -->
    <div class="diagnostic-item">
      <span>Dashboard Cards:</span>
      <span :class="{ 'status-ok': dashboardCardsVisible, 'status-error': !dashboardCardsVisible }">
        {{ dashboardCardsVisible ? '✓' : '✗' }}
      </span>
    </div>
    
    <!-- Spacing Check -->
    <div class="diagnostic-item">
      <span>Proper Spacing:</span>
      <span :class="{ 'status-ok': properSpacing, 'status-error': !properSpacing }">
        {{ properSpacing ? '✓' : '✗' }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const topbarVisible = ref(false)
const sidebarVisible = ref(false)
const dashboardCardsVisible = ref(false)
const properSpacing = ref(false)

let observer: MutationObserver | null = null

const checkUIElements = () => {
  // Check topbar
  const topbar = document.querySelector('.assistui-topbar, .global-toolbar, .usx-surface-header')
  topbarVisible.value = !!topbar
  
  // Check sidebar
  const sidebar = document.querySelector('.vault-sidebar, .assistui-conv-sidebar, .developer-tabs')
  sidebarVisible.value = !!sidebar
  
  // Check dashboard cards
  const dashboardCards = document.querySelectorAll('.dashboard-card, .mission-card, .kanban-card')
  dashboardCardsVisible.value = dashboardCards.length > 0
  
  // Check spacing
  const topbarEl = topbar as HTMLElement
  const sidebarEl = sidebar as HTMLElement
  const bodyEl = document.querySelector('.usx-surface-body, .assistui-body, .developer-content') as HTMLElement
  
  if (topbarEl && sidebarEl && bodyEl) {
    const topbarHeight = topbarEl.offsetHeight
    const sidebarWidth = sidebarEl.offsetWidth
    const bodyPadding = parseInt(getComputedStyle(bodyEl).padding)
    
    properSpacing.value = topbarHeight >= 40 && sidebarWidth >= 200 && bodyPadding >= 10
  }
}

onMounted(() => {
  checkUIElements()
  
  observer = new MutationObserver(checkUIElements)
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'style']
  })
  
  // Check every 2 seconds
  setInterval(checkUIElements, 2000)
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
})
</script>

<style scoped>
.diagnostic-panel {
  position: fixed;
  top: var(--usx-topbar-height);
  right: var(--usx-spacing-sm);
  z-index: 9999;
  background: color-mix(in srgb, var(--usx-color-surface) 90%, transparent);
  color: var(--usx-color-on-surface);
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  box-shadow: var(--usx-shadow-lg);
}

.diagnostic-item {
  display: flex;
  justify-content: space-between;
  padding: var(--usx-spacing-xs) 0;
}

.status-ok {
  color: var(--usx-color-success);
}

.status-error {
  color: var(--usx-color-danger);
}
</style>