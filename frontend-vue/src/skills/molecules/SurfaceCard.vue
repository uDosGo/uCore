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
  padding: var(--usx-spacing-lg);
  background: var(--pico-card-background-color);
  border: 1px solid rgba(88, 166, 255, 0.08);
  border-radius: var(--usx-border-radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
}

.surface-card:hover {
  background: #1a2332;
  border-color: rgba(88, 166, 255, 0.2);
  transform: translateY(-2px);
}

.surface-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--usx-border-radius-md);
  background: rgba(88, 166, 255, 0.08);
  color: rgba(88, 166, 255, 0.8);
  flex-shrink: 0;
}

.surface-card:hover .surface-card__icon {
  background: rgba(88, 166, 255, 0.12);
  color: rgba(88, 166, 255, 1);
}

.surface-card__content {
  flex: 1;
  min-width: 0;
}

.surface-card__title {
  font-size: var(--usx-font-size-lg);
  font-weight: 600;
  margin: 0;
  color: var(--pico-color);
}

.surface-card__description {
  font-size: var(--usx-font-size-sm);
  color: var(--pico-muted-color);
  margin-top: var(--usx-spacing-xs);
}

.surface-card__arrow {
  color: rgba(88, 166, 255, 0.5);
  flex-shrink: 0;
  transition: color 0.15s ease;
}

.surface-card:hover .surface-card__arrow {
  color: rgba(88, 166, 255, 0.8);
}
</style>
