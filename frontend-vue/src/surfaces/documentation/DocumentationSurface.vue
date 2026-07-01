<template>
  <div class="surface">
    <div class="surface__tabs">
      <button
        v-for="tab in DOC_TABS"
        :key="tab.id"
        class="surface__tab"
        :class="{ 'surface__tab--active': activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <UIcon :name="tab.icon" />
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <div class="surface__content">
      <!-- Learning Hub -->
      <div v-if="activeTab === 'learning'">
        <h2 style="margin:0 0 var(--usx-spacing-xs);font-size:1.5rem">Learning Hub</h2>
        <p class="usx-mb-lg" style="color:var(--pico-muted-color)">Tutorials, guides, courses, and skill tracking for mastering uCore.</p>
        <div class="docs-grid">
          <div v-for="course in courses" :key="course.id" class="docs-card">
            <UIcon :name="course.icon" />
            <h4>{{ course.title }}</h4>
            <p>{{ course.description }}</p>
            <UBadge :type="course.status === 'completed' ? 'success' : course.status === 'in-progress' ? 'warning' : 'info'" size="sm">
              {{ course.status }}
            </UBadge>
          </div>
        </div>
      </div>

      <!-- Guide & Docs -->
      <div v-else-if="activeTab === 'guide'">
        <h2 style="margin:0 0 var(--usx-spacing-xs);font-size:1.5rem">Guide & Docs</h2>
        <p class="usx-mb-lg" style="color:var(--pico-muted-color)">Jekyll-based documentation site.</p>
        <div class="docs-iframes">
          <div class="docs-iframe-card">
            <h4>DevStudio Docs</h4>
            <iframe src="file:///Users/fredbook/Public/doc-sites/DevStudio-docs/_site/index.html" title="DevStudio Docs" />
          </div>
          <div class="docs-iframe-card">
            <h4>Guide</h4>
            <iframe src="file:///Users/fredbook/Public/doc-sites/DevStudio-docs/_site/guide/index.html" title="Guide" />
          </div>
        </div>
      </div>

      <!-- API Reference -->
      <div v-else-if="activeTab === 'api'">
        <h2 style="margin:0 0 var(--usx-spacing-xs);font-size:1.5rem">API Reference</h2>
        <p class="usx-mb-lg" style="color:var(--pico-muted-color)">Backend API endpoints and MCP tool registry.</p>
        <div class="docs-api-list">
          <div v-for="ep in apiEndpoints" :key="ep.path" class="api-endpoint">
            <UBadge :type="ep.method === 'GET' ? 'success' : 'warning'" size="sm">{{ ep.method }}</UBadge>
            <code>{{ ep.path }}</code>
            <span>{{ ep.description }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

const activeTab = ref('learning')

const DOC_TABS = [
  { id: 'learning', label: 'Learning Hub', icon: 'school' },
  { id: 'guide', label: 'Guide & Docs', icon: 'menu_book' },
  { id: 'api', label: 'API Reference', icon: 'code' },
]

const courses = [
  { id: '1', title: 'Vue 3 Fundamentals', icon: 'school', description: 'Learn Vue 3 Composition API, reactivity, and component design', status: 'completed' },
  { id: '2', title: 'Pinia State Management', icon: 'storage', description: 'Master Pinia stores for predictable state', status: 'completed' },
  { id: '3', title: 'Skills-First Architecture', icon: 'extension', description: 'Build reusable AI-friendly component libraries', status: 'in-progress' },
  { id: '4', title: 'MCP Protocol Deep Dive', icon: 'sync_alt', description: 'Understand the Model Context Protocol', status: 'available' },
  { id: '5', title: 'GridCore & Spatial Algebra', icon: 'grid_view', description: 'Grid rendering and spatial computation engine', status: 'available' },
  { id: '6', title: 'BBCSDL Terminal & Teletext', icon: 'terminal', description: 'Retro computing with BBC BASIC and Ceefax', status: 'available' },
]

const apiEndpoints = [
  { method: 'GET', path: '/api/status', description: 'Snackbar server status' },
  { method: 'GET', path: '/api/knowledge', description: 'List knowledge documents' },
  { method: 'POST', path: '/api/chat', description: 'Send chat message (non-streaming)' },
  { method: 'GET', path: '/api/chat/stream', description: 'Stream chat response (SSE)' },
  { method: 'POST', path: '/api/skills/tasker_sync/run', description: 'Run tasker sync skill' },
  { method: 'POST', path: '/api/skills/vault_sync/run', description: 'Run vault sync skill' },
  { method: 'GET', path: '/health', description: 'uCore backend health check' },
  { method: 'GET', path: '/api/models', description: 'List available LLM models' },
]
</script>

<style scoped>
/* Surface-specific overrides only — layout handled by .surface__* classes */

.docs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--usx-spacing-md);
}

.docs-card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-md);
  background: var(--pico-card-background-color);
  border-radius: var(--usx-border-radius-lg);
}

.docs-card h4 {
  margin: 0;
  font-size: var(--usx-font-size-base);
}

.docs-card p {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  margin: 0;
}

.docs-iframes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--usx-spacing-md);
}

.docs-iframe-card {
  background: var(--pico-background-color);
  border-radius: var(--usx-border-radius-lg);
  overflow: hidden;
}

.docs-iframe-card h4 {
  margin: 0;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  background: var(--pico-card-background-color);
}

.docs-iframe-card iframe {
  width: 100%;
  height: 400px;
  border: none;
  background: #fff;
}

.docs-api-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.api-endpoint {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  border-radius: var(--usx-border-radius-sm);
}

.api-endpoint code {
  font-family: monospace;
  font-size: var(--usx-font-size-sm);
  color: var(--pico-primary);
  min-width: 200px;
}

.api-endpoint span {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
}
</style>
