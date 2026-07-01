<template>
  <div class="system-page">
    <h2>System Page — {{ pageCode }}</h2>
    <p class="system-page-note">S-page / P-page renderer. Full port pending Wave 2.</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const pageCode = computed(() => route.path.replace('/', '').toUpperCase())
</script>

<style scoped>
.system-page { padding: var(--usx-spacing-lg); }
.system-page-note { color: var(--pico-muted-color, #8b949e); font-size: var(--usx-font-size-sm); }
</style>
