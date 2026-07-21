<template>
  <div class="surface">
    <div class="surface__topbar browserui-topbar">
      <div class="browserui-search-wrap">
        <UInput v-model="searchQuery" placeholder="Search the web..." />
      </div>
    </div>
    <div class="surface__content">
      <div v-if="filteredStacks.length === 0" class="browserui-empty">
        <UIcon name="search" class="browserui-empty-icon" />
        <p>No results found</p>
      </div>
      <div v-for="stack in filteredStacks" :key="stack.id" class="browserui-stack">
        <div class="browserui-stack-header">
          <UIcon :name="stack.icon" class="browserui-stack-icon" />
          <h3>{{ stack.title }}</h3>
          <UBadge type="info" circle>{{ stack.items.length }}</UBadge>
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import UInput from '../../skills/atoms/UInput.vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'
const searchQuery = ref('')
const loading = ref(true)

interface StackItem {
  id: string; title: string; url: string; description: string; tags: string[]
}

const stacks = ref<Array<{ id: string; title: string; icon: string; items: StackItem[] }>>([])

const DEFAULT_STACKS = [
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
]

async function fetchBookmarks() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/knowledge?type=bookmark`, {
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) {
      const data = await res.json()
      const items = (data.items || data || []).map((b: any) => ({
        id: b.id || b.url,
        title: b.title || b.name || 'Untitled',
        url: b.url || b.link || '#',
        description: b.description || b.summary || '',
        tags: (b.tags || b.keywords || []).map((t: string) => t.startsWith('#') ? t : `#${t}`),
      }))
      if (items.length > 0) {
        stacks.value = [{ id: 'bookmarks', title: 'Bookmarks', icon: 'bookmark', items }]
        return
      }
    }
  } catch { /* backend offline, use defaults */ }
  stacks.value = DEFAULT_STACKS
  loading.value = false
}

onMounted(() => { fetchBookmarks() })

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
/* ─── Topbar: search box centered ───────────────────────────────── */
.browserui-topbar {
  display: flex;
  align-items: center;
  justify-content: center;
  height: auto;
  padding: var(--usx-spacing-md) var(--usx-spacing-xl);
}

.browserui-search-wrap {
  display: flex;
  justify-content: center;
  width: 100%;
  max-width: 40ch;
}

.browserui-search-wrap .u-input {
  width: 100%;
}

/* ─── Empty state ──────────────────────────────────────────────── */
.browserui-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-3xl) 0;
  color: var(--usx-color-on-surface-muted);
}

.browserui-empty-icon {
  font-size: 3em;
  margin-bottom: var(--usx-spacing-md);
  opacity: 0.4;
}

.browserui-empty p {
  font-size: var(--usx-font-size-base);
  margin: 0;
}

/* ─── Stack sections ───────────────────────────────────────────── */
.browserui-stack + .browserui-stack {
  margin-top: var(--usx-spacing-2xl);
}

.browserui-stack-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-md);
}

.browserui-stack-icon {
  font-size: 1.5em;
  color: var(--usx-color-on-surface-muted);
}

.browserui-stack-header h3 {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0;
  flex: 1;
}

/* ─── Card grid ────────────────────────────────────────────────── */
.browserui-cards {
  --browserui-card-column-min: calc(var(--usx-touch-min) * 4.5);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--browserui-card-column-min)), 1fr));
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.browserui-card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  text-decoration: none;
  color: inherit;
  min-width: 0;
  transition: border-color var(--usx-transition-fast), transform var(--usx-transition-fast), box-shadow var(--usx-transition-fast);
}

.browserui-card:hover {
  border-color: var(--usx-color-primary);
  transform: translateY(calc(var(--usx-spacing-1) * -1));
  box-shadow: var(--usx-shadow-md);
}

.browserui-card-title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  overflow-wrap: anywhere;
}

.browserui-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  line-height: var(--usx-line-height-normal);
  overflow-wrap: anywhere;
}

.browserui-card-tags {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: var(--usx-spacing-xs);
}

.browserui-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-full);
  color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-medium);
  line-height: var(--usx-line-height-none);
  white-space: nowrap;
}
</style>
