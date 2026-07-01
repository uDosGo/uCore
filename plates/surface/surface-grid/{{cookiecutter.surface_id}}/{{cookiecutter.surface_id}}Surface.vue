<template>
  <div class="surface">
    <!-- Toolbar -->
    <header class="surface__toolbar">
      <h1 class="surface__topbar-title">{{cookiecutter.surface_title}}</h1>
      <div class="surface__toolbar-actions">
        <slot name="toolbar-actions" />
      </div>
    </header>

    <!-- Grid/canvas area -->
    <div class="surface__canvas">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component {{cookiecutter.surface_id}}Surface
 * @description {{cookiecutter.surface_description}}
 * Generated from surface-grid plate template.
 * Uses USX surface classes from usx-standard.css.
 * @category surfaces
 * @usage Routed at '{{cookiecutter.route_path}}'
 */
</script>

<style scoped>
/* Surface-specific overrides only — layout handled by .surface__* classes */
</style>
