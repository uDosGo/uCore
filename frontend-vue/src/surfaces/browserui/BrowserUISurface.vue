<template>
  <div class="surface">
    <div class="surface__toolbar">
      <h1 class="surface__topbar-title">Browser</h1>
      <div class="surface__toolbar-actions">
        <UInput v-model="searchQuery" placeholder="Search the web..." class="browserui-search-input" />
      </div>
    </div>
    <div class="surface__content">
      <div class="browserui-stacks">
        <div v-for="stack in filteredStacks" :key="stack.id" class="browserui-stack">
          <div class="browserui-stack-header">
            <UIcon :name="stack.icon" />
            <h3>{{ stack.title }}</h3>
            <UBadge type="info" size="sm">{{ stack.items.length }}</UBadge>
          </div>
          <div class="browserui-cards">
            <a
              v-for="item in stack.items"
              :key="item.id"
              :href="item.url"
              target="_blank"
              rel="noopener"
              class="browserui-card"
            >
              <div class="browserui-card-title">{{ item.title }}</div>
              <div class="browserui-card-desc">{{ item.description }}</div>
              <div class="browserui-card-tags">
                <span v-for="tag in item.tags" :key="tag" class="browserui-tag">{{ tag }}</span>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import UInput from '../../skills/atoms/UInput.vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

const searchQuery = ref('')

const stacks = ref([
  {
    id: 'research', title: 'Research', icon: 'search',
    items: [
      { id: 'r1', title: 'MCP Protocol Spec', url: 'https://modelcontextprotocol.io', description: 'Official MCP specification', tags: ['#mcp', '#protocol'] },
      { id: 'r2', title: 'Vue 3 Docs', url: 'https://vuejs.org', description: 'Vue 3 framework documentation', tags: ['#vue', '#frontend'] },
      { id: 'r3', title: 'Rust Async Book', url: 'https://rust-lang.github.io/async-book/', description: 'Async Rust guide', tags: ['#rust', '#async'] },
    ],
  },
  {
    id: 'bookmarks', title: 'Bookmarks', icon: 'bookmark',
    items: [
      { id: 'b1', title: 'GitHub Copilot Docs', url: 'https://docs.github.com/en/copilot', description: 'Copilot documentation', tags: ['#tools', '#ai'] },
      { id: 'b2', title: 'MDN Web Docs', url: 'https://developer.mozilla.org', description: 'Web platform reference', tags: ['#reference', '#web'] },
      { id: 'b3', title: 'Docker Compose Docs', url: 'https://docs.docker.com/compose/', description: 'Multi-container apps', tags: ['#docker', '#devops'] },
      { id: 'b4', title: 'Tailwind CSS Docs', url: 'https://tailwindcss.com/docs', description: 'Utility-first CSS', tags: ['#css', '#frontend'] },
    ],
  },
  {
    id: 'learning', title: 'Learning', icon: 'school',
    items: [
      { id: 'l1', title: 'Pinia Docs', url: 'https://pinia.vuejs.org', description: 'Vue state management', tags: ['#vue', '#state'] },
      { id: 'l2', title: 'Vite Docs', url: 'https://vitejs.dev', description: 'Next-gen frontend tooling', tags: ['#build', '#frontend'] },
      { id: 'l3', title: 'CodeMirror 6', url: 'https://codemirror.net', description: 'Code editor component', tags: ['#editor', '#code'] },
    ],
  },
])

const filteredStacks = computed(() => {
  if (!searchQuery.value) return stacks.value
  const q = searchQuery.value.toLowerCase()
  return stacks.value.map(stack => ({
    ...stack,
    items: stack.items.filter(item =>
      item.title.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q) ||
      item.tags.some(t => t.toLowerCase().includes(q))
    ),
  })).filter(stack => stack.items.length > 0)
})
</script>

<style scoped>
.browserui-stacks {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xl);
}

.browserui-stack-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-md);
}

.browserui-stack-header h3 {
  font-size: var(--usx-font-size-lg);
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.browserui-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--usx-spacing-sm);
}

.browserui-card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-md);
  background: var(--pico-card-background-color);
  border-radius: var(--usx-border-radius-lg);
  text-decoration: none;
  color: inherit;
  transition: all 0.15s ease;
}

.browserui-card:hover {
  border-color: var(--pico-primary);
  transform: translateY(-1px);
}

.browserui-card-title {
  font-size: var(--usx-font-size-sm);
  font-weight: 600;
}

.browserui-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
}

.browserui-card-tags {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.browserui-tag {
  font-size: var(--usx-font-size-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--pico-border-color);
  border-radius: var(--usx-border-radius-sm);
  color: var(--pico-muted-color);
}

.browserui-search-input {
  max-width: 500px;
}
</style>
