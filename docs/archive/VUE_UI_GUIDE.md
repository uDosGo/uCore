# Vue UI Detection and Repair Guide

## Common Issues and Solutions

### 1. Topbar Not Visible

**Symptoms:**
- Topbar elements are missing or overlapping
- No sticky navigation at top of page

**Detection:**
```javascript
// Check if topbar exists
const topbar = document.querySelector('.assistui-topbar, .global-toolbar')
console.log('Topbar visible:', !!topbar)
```

**Fix:**
```css
.assistui-topbar, .global-toolbar {
  display: flex !important;
  min-height: 48px !important;
  position: sticky !important;
  top: 0 !important;
  z-index: 100 !important;
}
```

### 2. Sidebar Not Showing

**Symptoms:**
- No sidebar navigation visible
- Developer/mission controls missing

**Detection:**
```javascript
const sidebar = document.querySelector('.vault-sidebar, .assistui-conv-sidebar')
console.log('Sidebar visible:', !!sidebar)
if (sidebar) console.log('Width:', sidebar.offsetWidth)
```

**Fix:**
```css
.vault-sidebar, .assistui-conv-sidebar {
  display: block !important;
  visibility: visible !important;
  width: 280px !important;
  min-width: 280px !important;
  overflow: hidden !important;
}
```

### 3. Dashboard Cards Missing

**Symptoms:**
- No mission control cards
- Empty dashboard

**Detection:**
```javascript
const cards = document.querySelectorAll('.dashboard-card, .mission-card')
console.log('Dashboard cards:', cards.length)
```

**Fix:**
```css
.dashboard-surface__grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)) !important;
  gap: 16px !important;
}
```

### 4. Spacing Issues

**Symptoms:**
- Elements too close together
- No breathing room between components

**Detection:**
```javascript
const body = document.querySelector('.usx-surface-body')
if (body) {
  const style = getComputedStyle(body)
  console.log('Padding:', style.padding)
  console.log('Gap:', style.gap)
}
```

**Fix:**
```css
.usx-surface-body, .assistui-body, .developer-content {
  display: flex !important;
  flex-direction: column !important;
  gap: 12px !important;
  padding: 16px !important;
}
```

### 5. Element Visibility Check

**Comprehensive Detection Script:**
```javascript
function checkUIHealth() {
  const results = {
    topbar: document.querySelector('.assistui-topbar') !== null,
    sidebar: document.querySelector('.vault-sidebar') !== null,
    dashboardCards: document.querySelectorAll('.mission-card').length > 0,
    kanbanBoard: document.querySelector('.kanban-board') !== null,
    hasProperSpacing: false
  }
  
  // Check spacing
  const body = document.querySelector('.usx-surface-body')
  if (body) {
    const style = getComputedStyle(body)
    const gap = style.gap
    const padding = style.padding
    results.hasProperSpacing = gap !== 'normal' && padding !== '0px'
  }
  
  return results
}

// Run check
const health = checkUIHealth()
console.log('UI Health:', health)
```

## Automated Repair Process

### Step 1: Detect Issues
1. Check if critical UI elements exist
2. Verify proper CSS classes are applied
3. Validate spacing and layout

### Step 2: Apply Fixes
```javascript
// Apply fixes based on detected issues
if (!health.topbar) {
  applyTopbarFix()
}
if (!health.sidebar) {
  applySidebarFix()
}
if (!health.dashboardCards) {
  applyDashboardFix()
}
if (!health.hasProperSpacing) {
  applySpacingFix()
}
```

### Step 3: Verify Fixes
```javascript
// Re-check after fixes
setTimeout(() => {
  const newHealth = checkUIHealth()
  console.log('Post-repair health:', newHealth)
}, 1000)
```

## Vue Component Best Practices

### 1. Proper Component Structure
```vue
<template>
  <div class="surface-container">
    <div class="topbar-section">
      <!-- Topbar content -->
    </div>
    <div class="main-content">
      <div class="sidebar">
        <!-- Sidebar content -->
      </div>
      <div class="primary-content">
        <!-- Main content -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const isMounted = ref(false)

onMounted(() => {
  isMounted.value = true
  // Initialize UI components
})
</script>
```

### 2. CSS Scoped Properly
```vue
<style scoped>
/* Use scoped styles to prevent conflicts */
.topbar-section {
  display: flex;
  min-height: 48px;
}

.main-content {
  display: flex;
  flex: 1;
}

.sidebar {
  width: 280px;
  min-width: 280px;
}
</style>
```

### 3. Responsive Design
```vue
<template>
  <div :class="['container', { 'mobile': isMobile }]">
    <!-- Responsive content -->
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const isMobile = ref(false)

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
}

.mobile {
  flex-direction: column;
}
</style>
```

## Debugging Tools

### 1. Element Inspector
```javascript
// Log all critical elements
function logCriticalElements() {
  const elements = {
    topbar: '.assistui-topbar, .global-toolbar',
    sidebar: '.vault-sidebar, .assistui-conv-sidebar',
    dashboard: '.dashboard-surface__grid',
    kanban: '.kanban-board',
    main: '.usx-surface-body, .assistui-body'
  }
  
  Object.entries(elements).forEach(([key, selector]) => {
    const el = document.querySelector(selector)
    console.log(`${key}:`, el ? '✓' : '✗', el)
  })
}
```

### 2. CSS Validation
```javascript
function validateCSS() {
  const stylesheets = Array.from(document.styleSheets)
  const missingRules = []
  
  stylesheets.forEach(sheet => {
    try {
      const rules = Array.from(sheet.cssRules || sheet.rules)
      const hasCritical = rules.some(rule => 
        rule.selectorText && (
          rule.selectorText.includes('.assistui-topbar') ||
          rule.selectorText.includes('.vault-sidebar') ||
          rule.selectorText.includes('.dashboard-surface')
        )
      )
      if (!hasCritical) {
        missingRules.push(sheet.href || 'inline')
      }
    } catch (e) {
      // Cross-origin stylesheet
    }
  })
  
  return missingRules
}
```

## Quick Fix Commands

```bash
# Clear cache and reload
npm run build && npm run preview

# Check for CSS conflicts
npx tailwindcss --config tailwind.config.js --css src/styles.css --output dist.css

# Validate Vue components
npx vue-tsc --noEmit
```

## Prevention Tips

1. **Always use scoped CSS** to prevent conflicts
2. **Test on multiple viewports** (mobile, tablet, desktop)
3. **Use CSS variables** for consistent theming
4. **Implement proper error boundaries** in Vue components
5. **Add monitoring** for UI health checks