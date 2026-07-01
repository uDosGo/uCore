<template>
  <div class="surface">
    <!-- Tab bar -->
    <div class="surface__tabs">
      <button
        v-for="tab in TABS"
        :key="tab.id"
        class="surface__tab"
        :class="{ 'surface__tab--active': store.activeTab === tab.id }"
        @click="store.setTab(tab.id)"
      >
        <UIcon :name="tab.icon" :size="14" />
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- Panel content -->
    <div class="surface__content">
      <Panel1 v-if="store.activeTab === 'panel1'" />
      <Panel2 v-else-if="store.activeTab === 'panel2'" />
      <Panel3 v-else-if="store.activeTab === 'panel3'" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component {{cookiecutter.surface_id}}Surface
 * @description {{cookiecutter.surface_description}}
 * Generated from surface-tabbed plate template.
 * Uses USX surface classes from usx-standard.css.
 * @category surfaces
 * @usage Routed at '{{cookiecutter.route_path}}'
 */
import UIcon from '../../skills/atoms/UIcon.vue'
import { use{{cookiecutter.surface_id|capitalize}}Store, TABS } from '../../stores/{{cookiecutter.surface_id}}'
import Panel1 from './panels/Panel1.vue'
import Panel2 from './panels/Panel2.vue'
import Panel3 from './panels/Panel3.vue'

const store = use{{cookiecutter.surface_id|capitalize}}Store()
</script>

<style scoped>
/* Surface-specific overrides only — layout handled by .surface__* classes */
</style>
