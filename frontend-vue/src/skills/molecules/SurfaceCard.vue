<template>
  <div class="surface-card" :style="{ '--accent': surface.color }" @click="emit('click')">
    <div class="surface-card__icon">
      <UIcon :name="surface.icon" />
    </div>
    <div class="surface-card__content">
      <h3 class="surface-card__title">{{ surface.title }}</h3>
      <p class="surface-card__description">{{ surface.description }}</p>
    </div>
    <UIcon name="chevron-right" class="surface-card__arrow" />
  </div>
</template>

<script setup lang="ts">
/**
 * @component SurfaceCard
 * @description Reusable surface card for the dashboard grid.
 * @category molecules
 * @props {SurfaceCard} surface - Surface data object
 * @emits {} click - Card clicked
 * @usage <SurfaceCard :surface="surface" @click="navigate(surface.route)" />
 */
import UIcon from '../atoms/UIcon.vue'
import type { SurfaceCard } from '../../types'

interface Props {
  surface: SurfaceCard
}

defineProps<Props>()

const emit = defineEmits<{
  click: []
}>()
</script>

<style scoped>
.surface-card {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-lg);
  padding: var(--usx-card-padding);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  transition: background var(--usx-transition-base), border-color var(--usx-transition-base), box-shadow var(--usx-transition-base), transform var(--usx-transition-base);
  box-sizing: border-box;
  min-height: var(--usx-touch-min);
}

.surface-card:hover {
  background: var(--usx-color-surface-hover);
  border-color: var(--usx-color-primary);
  transform: translateY(calc(var(--usx-spacing-1) * -1));
  box-shadow: 0 var(--usx-spacing-sm) var(--usx-spacing-lg) color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent);
}

.surface-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
  flex-shrink: 0;
  font-size: var(--usx-icon-size-xl);
}

.surface-card:hover .surface-card__icon {
  background: var(--usx-color-primary-disabled);
  color: var(--usx-color-primary);
}

.surface-card__content {
  flex: 1;
  min-width: 0;
}

.surface-card__title {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0;
  color: var(--usx-color-on-surface);
}

.surface-card__description {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-top: var(--usx-spacing-xs);
}

.surface-card__arrow {
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
  transition: color var(--usx-transition-base);
  font-size: var(--usx-icon-size);
}

.surface-card:hover .surface-card__arrow {
  color: var(--usx-color-primary);
}
</style>
