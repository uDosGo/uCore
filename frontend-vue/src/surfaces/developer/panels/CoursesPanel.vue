<template>
  <div class="usx-section">
    <div class="usx-flex-between">
      <h3>Course Registry</h3>
      <div class="usx-flex-row usx-gap-sm">
        <span class="usx-badge usx-badge--accent">{{ filteredCourses.length }} courses</span>
        <button class="usx-btn--primary" @click="refresh">
          <span class="material-symbols-outlined">refresh</span>
          Refresh
        </button>
      </div>
    </div>

    <p class="usx-mt-sm courses-muted-copy">
      Rated inventory of uCode documentation — completeness, level, and relevance to uCode.
      <strong>{{ summary.relevance_high_90_plus }}</strong> highly relevant,
      <strong>{{ summary.relevance_medium_60_89 }}</strong> medium,
      <strong>{{ summary.relevance_low_below_60 }}</strong> low relevance.
    </p>

    <!-- Filters -->
    <div class="usx-flex-row usx-gap-sm usx-mt-md courses-wrap">
      <select v-model="filterCategory" class="courses-control">
        <option value="">All Categories</option>
        <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
      </select>
      <select v-model="filterLevel" class="courses-control">
        <option value="">All Levels</option>
        <option value="beginner">Beginner</option>
        <option value="average">Average</option>
        <option value="advanced">Advanced</option>
      </select>
      <select v-model="filterRelevance" class="courses-control">
        <option value="">All Relevance</option>
        <option value="90">High (90-100)</option>
        <option value="60">Medium (60-89)</option>
        <option value="0">Low (0-59)</option>
      </select>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search courses..."
        class="courses-search"
      />
    </div>

    <!-- Summary Cards -->
    <div class="usx-grid usx-grid--dense usx-mt-md">
      <div class="usx-card">
        <span class="courses-stat-value courses-success-copy">
          {{ summary.relevance_high_90_plus }}
        </span>
        <span class="courses-stat-label">Highly Relevant</span>
      </div>
      <div class="usx-card">
        <span class="courses-stat-value courses-warning-copy">
          {{ summary.relevance_medium_60_89 }}
        </span>
        <span class="courses-stat-label">Medium Relevance</span>
      </div>
      <div class="usx-card">
        <span class="courses-stat-value courses-danger-copy">
          {{ summary.relevance_low_below_60 }}
        </span>
        <span class="courses-stat-label">Low Relevance</span>
      </div>
      <div class="usx-card">
        <span class="courses-stat-value">
          {{ summary.total_courses }}
        </span>
        <span class="courses-stat-label">Total Courses</span>
      </div>
    </div>

    <!-- Category Breakdown -->
    <div v-if="filterCategory === ''" class="usx-mt-md">
      <div class="usx-flex-row usx-gap-sm courses-wrap">
        <button
          v-for="(count, cat) in allCategories"
          :key="cat"
          class="usx-badge"
          :class="{ 'usx-badge--accent': filterCategory === '' }"
          class="courses-clickable"
          @click="filterCategory = (filterCategory === cat) ? '' : cat"
        >
          {{ cat }}: {{ count }}
        </button>
      </div>
    </div>

    <!-- Top 12 by Relevance -->
    <div class="usx-mt-lg">
      <h4>Top by Relevance</h4>
      <div class="usx-grid usx-grid--dense usx-mt-sm">
        <div
          v-for="item in topByRelevance"
          :key="item.file"
          class="usx-card"
          @click="selectedFile = item.file"
        >
          <div class="usx-flex-between">
            <div class="usx-flex-row">
              <span class="material-symbols-outlined courses-icon-sm courses-success-copy">verified</span>
              <span class="courses-title-medium">{{ item.title }}</span>
            </div>
            <span class="usx-badge usx-badge--accent">{{ item.relevance }}%</span>
          </div>
          <div class="usx-flex-row usx-gap-xs usx-mt-sm courses-row-xs">
            <span class="usx-badge courses-badge--compact">{{ item.level }}</span>
            <span class="usx-badge courses-badge--compact">complete: {{ item.completeness }}%</span>
            <span class="courses-muted-copy">{{ item.category }}</span>
          </div>
          <div v-if="item.notes" class="usx-mt-sm courses-meta-text">
            {{ item.notes }}
          </div>
        </div>
      </div>
    </div>

    <!-- Filtered Course List -->
    <div class="usx-mt-lg">
      <div class="usx-flex-between">
        <h4>Filtered Courses ({{ filteredCourses.length }})</h4>
        <span v-if="searchQuery" class="usx-badge">search: "{{ searchQuery }}"</span>
      </div>
      <div
        v-if="filteredCourses.length === 0"
        class="usx-compact usx-mt-sm courses-empty"
      >
        No courses match your filters. Try adjusting the criteria.
      </div>
      <div v-else class="usx-grid usx-grid--dense usx-mt-sm">
        <div
          v-for="item in paginatedCourses"
          :key="item.file"
          class="usx-card"
        >
          <div class="usx-flex-between">
            <div class="usx-flex-row">
              <span class="material-symbols-outlined courses-icon-sm"
                :class="relevanceToneClass(item.relevance)"
              >
                {{ relevanceIcon(item.relevance) }}
              </span>
              <span class="courses-title-medium">{{ item.title }}</span>
            </div>
          </div>
          <div class="usx-flex-row usx-gap-xs usx-mt-sm courses-row-xs">
            <span
              class="usx-badge courses-badge--compact"
              :class="{
                'usx-badge--accent': item.level === 'beginner',
                'usx-badge--success': item.level === 'advanced'
              }"
            >
              {{ item.level }}
            </span>
            <span class="usx-badge courses-badge--compact">
              C:{{ item.completeness }}%
            </span>
            <span class="usx-badge"
              :class="['courses-badge--compact', relevanceBadgeClass(item.relevance)]"
            >
              R:{{ item.relevance }}%
            </span>
            <span class="courses-muted-copy">{{ item.category }}</span>
          </div>
          <div v-if="item.notes" class="usx-mt-sm courses-meta-text">
            {{ item.notes.slice(0, 80) }}{{ item.notes.length > 80 ? '...' : '' }}
          </div>
          <div v-if="item.topics?.length" class="usx-flex-row usx-gap-xs usx-mt-sm courses-wrap">
            <span
              v-for="topic in item.topics.slice(0, 4)"
              :key="topic"
              class="usx-badge courses-badge--compact"
            >
              {{ topic }}
            </span>
            <span v-if="item.topics.length > 4" class="courses-meta-text">
              +{{ item.topics.length - 4 }} more
            </span>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="usx-flex-center usx-mt-md usx-gap-sm">
        <button
          class="usx-btn--primary courses-page-btn"
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          <span class="material-symbols-outlined">chevron_left</span>
        </button>
        <span class="courses-page-meta">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
        <button
          class="usx-btn--primary courses-page-btn"
          :disabled="currentPage === totalPages"
          @click="currentPage++"
        >
          <span class="material-symbols-outlined">chevron_right</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface CourseItem {
  file: string
  title: string
  completeness: number
  level: string
  relevance: number
  topics: string[]
  notes?: string
  category?: string
}

interface CourseCategory {
  [key: string]: CourseItem[]
}

interface RegistryData {
  version: string
  description: string
  courses: CourseCategory
  summary: {
    total_courses: number
    relevance_high_90_plus: number
    relevance_medium_60_89: number
    relevance_low_below_60: number
    top_by_relevance: string[]
  }
}

const registry = ref<RegistryData | null>(null)
const allCourses = ref<CourseItem[]>([])
const filterCategory = ref('')
const filterLevel = ref('')
const filterRelevance = ref('')
const searchQuery = ref('')
const selectedFile = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const loading = ref(false)
const error = ref<string | null>(null)

// Hard-coded registry data (seeds/course-registry.json)
const defaultData: RegistryData = {
  version: '1.0.0',
  description: 'Course Registry',
  courses: {
    basic: [],
    gridcore: [],
    spatial: [],
    tutorials: [],
    'learning-pathway': [],
    'top-level': []
  },
  summary: {
    total_courses: 56,
    relevance_high_90_plus: 24,
    relevance_medium_60_89: 19,
    relevance_low_below_60: 13,
    top_by_relevance: []
  }
}

const summary = computed(() => registry.value?.summary || defaultData.summary)

const categories = computed(() => Object.keys(registry.value?.courses || {}))

const allCategories = computed(() => {
  const counts: Record<string, number> = {}
  for (const c of allCourses.value) {
    const cat = c.category || 'other'
    counts[cat] = (counts[cat] || 0) + 1
  }
  return counts
})

const topByRelevance = computed(() => {
  return [...allCourses.value]
    .sort((a, b) => b.relevance - a.relevance)
    .slice(0, 12)
})

const filteredCourses = computed(() => {
  let items = allCourses.value

  if (filterCategory.value) {
    items = items.filter(c => c.category === filterCategory.value)
  }
  if (filterLevel.value) {
    items = items.filter(c => c.level === filterLevel.value)
  }
  if (filterRelevance.value) {
    const threshold = parseInt(filterRelevance.value)
    if (threshold === 90) {
      items = items.filter(c => c.relevance >= 90)
    } else if (threshold === 60) {
      items = items.filter(c => c.relevance >= 60 && c.relevance < 90)
    } else {
      items = items.filter(c => c.relevance < 60)
    }
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    items = items.filter(c =>
      c.title.toLowerCase().includes(q) ||
      c.topics.some(t => t.toLowerCase().includes(q)) ||
      (c.notes && c.notes.toLowerCase().includes(q)) ||
      c.file.toLowerCase().includes(q)
    )
  }

  return items
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredCourses.value.length / pageSize.value)))

const paginatedCourses = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredCourses.value.slice(start, start + pageSize.value)
})

function relevanceBadgeClass(relevance: number): string {
  if (relevance >= 90) return 'usx-badge--success'
  if (relevance >= 60) return 'usx-badge--accent'
  return 'usx-badge--error'
}

function relevanceToneClass(relevance: number): string {
  if (relevance >= 90) return 'courses-success-copy'
  if (relevance >= 60) return 'courses-warning-copy'
  return 'courses-danger-copy'
}

function relevanceIcon(relevance: number): string {
  if (relevance >= 90) return 'verified'
  if (relevance >= 60) return 'info'
  return 'warning'
}

function loadRegistry() {
  loading.value = true
  error.value = null

  try {
    // Load from seeds/course-registry.json
    // In production this would be fetched from backend API
    const raw = localStorage.getItem('ucode-course-registry')
    if (raw) {
      const data = JSON.parse(raw)
      registry.value = data
      flattenCourses(data.courses)
    } else {
      registry.value = defaultData
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to load course registry'
    registry.value = defaultData
  } finally {
    loading.value = false
  }
}

function flattenCourses(courses: CourseCategory) {
  const result: CourseItem[] = []
  for (const [category, items] of Object.entries(courses)) {
    for (const item of items) {
      result.push({ ...item, category })
    }
  }
  allCourses.value = result
}

function refresh() {
  currentPage.value = 1
  loadRegistry()
}

onMounted(() => {
  loadRegistry()
})
</script>

<style scoped>
.courses-badge--compact {
  padding: var(--usx-spacing-1) var(--usx-spacing-2);
  font-size: var(--usx-font-size-xs);
}

.courses-muted-copy {
  color: var(--usx-color-on-surface-muted);
}

.courses-meta-text {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.courses-wrap {
  flex-wrap: wrap;
}

.courses-control {
  min-height: var(--usx-touch-min);
  padding: 0 var(--usx-spacing-sm);
}

.courses-search {
  flex: 1;
  min-width: calc(var(--usx-spacing-2xl) * 6 + var(--usx-spacing-xs));
  min-height: var(--usx-touch-min);
  padding: 0 var(--usx-spacing-sm);
}

.courses-stat-value {
  font-size: var(--usx-font-size-3xl);
  font-weight: var(--usx-font-weight-bold);
}

.courses-stat-label {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.courses-success-copy {
  color: var(--usx-color-success);
}

.courses-warning-copy {
  color: var(--usx-color-warning);
}

.courses-danger-copy {
  color: var(--usx-color-danger);
}

.courses-clickable {
  cursor: pointer;
}

.courses-icon-sm {
  font-size: var(--usx-icon-size-sm);
}

.courses-title-medium {
  font-weight: var(--usx-font-weight-medium);
}

.courses-row-xs {
  font-size: var(--usx-font-size-xs);
}

.courses-empty {
  color: var(--usx-color-on-surface-muted);
  text-align: center;
}

.courses-page-btn {
  min-height: var(--usx-touch-min);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
}

.courses-page-meta {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}
</style>