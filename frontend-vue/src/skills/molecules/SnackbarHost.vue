<template>
  <Teleport to="body">
    <div class="snackbar-host">
      <TransitionGroup name="snackbar">
        <div
          v-for="item in snackbar.items"
          :key="item.id"
          class="snackbar-item"
          :class="`snackbar-item--${item.type}`"
          @click="snackbar.dismiss(item.id)"
        >
          <UIcon :name="iconForType(item.type)" />
          <span class="snackbar-item__message">{{ item.message }}</span>
          <button class="snackbar-item__close" @click.stop="snackbar.dismiss(item.id)">
            <UIcon name="close" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * @component SnackbarHost
 * @description Global snackbar notification host. Renders all active notifications.
 * Ported from SurfaceSnackbar.tsx (React).
 * @category molecules
 * @usage <SnackbarHost />
 */
import UIcon from '../atoms/UIcon.vue'
import { useSnackbarStore } from '../../stores/snackbar'
import type { SnackbarItem } from '../../stores/snackbar'

const snackbar = useSnackbarStore()

function iconForType(type: SnackbarItem['type']): string {
  const icons: Record<string, string> = {
    info: 'mdi:information',
    success: 'mdi:check-circle',
    warning: 'mdi:alert',
    error: 'mdi:alert-circle',
  }
  return icons[type]
}
</script>

<style scoped>
.snackbar-host {
  position: fixed;
  bottom: var(--usx-toast-offset);
  right: var(--usx-toast-offset);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  max-width: var(--usx-toast-max-width);
}

.snackbar-item {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-background);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
}

.snackbar-item--info { border-left: calc(var(--usx-border-width) + var(--usx-border-width-thick)) solid var(--usx-color-info); }
.snackbar-item--success { border-left: calc(var(--usx-border-width) + var(--usx-border-width-thick)) solid var(--usx-color-success); }
.snackbar-item--warning { border-left: calc(var(--usx-border-width) + var(--usx-border-width-thick)) solid var(--usx-color-warning); }
.snackbar-item--error { border-left: calc(var(--usx-border-width) + var(--usx-border-width-thick)) solid var(--usx-color-danger); }

.snackbar-item__message {
  flex: 1;
}

.snackbar-item__close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--usx-color-on-surface-muted);
  padding: var(--usx-spacing-xs);
}

/* Transitions */
.snackbar-enter-active,
.snackbar-leave-active {
  transition: opacity var(--usx-transition-slow), transform var(--usx-transition-slow);
}

.snackbar-enter-from {
  opacity: 0;
  transform: translateX(var(--usx-motion-distance-md));
}

.snackbar-leave-to {
  opacity: 0;
  transform: translateX(var(--usx-motion-distance-md));
}
</style>
