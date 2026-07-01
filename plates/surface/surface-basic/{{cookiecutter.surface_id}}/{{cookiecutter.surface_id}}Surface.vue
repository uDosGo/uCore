din<template>
  <div class="surface">
    <header class="surface__header">
      <h1 class="surface__title">{{cookiecutter.surface_title}}</h1>
      <p class="surface__description">{{cookiecutter.surface_description}}</p>
    </header>

    <div class="surface__content">
      <!-- Main content area -->
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component {{cookiecutter.surface_id}}Surface
 * @description {{cookiecutter.surface_description}}
 * Generated from surface-basic plate template.
 * Uses USX surface classes from usx-standard.css.
 * @category surfaces
 * @usage Routed at '{{cookiecutter.route_path}}'
 */
</script>

<style scoped>
/* Surface-specific overrides only — layout handled by .surface__* classes */
</style>
