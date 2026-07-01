<template>
  <div class="surface">
    <!-- Topbar -->
    <header class="surface__topbar">
      <h1 class="surface__topbar-title">{{cookiecutter.surface_title}}</h1>
      <div class="surface__topbar-actions">
        <slot name="actions" />
      </div>
    </header>

    <!-- Messages area -->
    <div class="surface__messages" ref="messagesRef">
      <div
        v-for="(msg, i) in store.messages"
        :key="i"
        class="surface__message"
        :class="`surface__message--${msg.role}`"
      >
        <div class="surface__message-content">
          {{ msg.content }}
        </div>
      </div>
      <div v-if="store.loading" class="usx-flex-center usx-p-md">
        <USpinner />
      </div>
    </div>

    <!-- Input area -->
    <footer class="surface__footer">
      <div class="surface__input-row">
        <UInput
          v-model="input"
          placeholder="Type a message..."
          @keydown.enter.prevent="send"
          :disabled="store.loading"
        />
        <UButton @click="send" :disabled="!input.trim() || store.loading">
          Send
        </UButton>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
/**
 * @component {{cookiecutter.surface_id}}Surface
 * @description {{cookiecutter.surface_description}}
 * Generated from surface-chat plate template.
 * Uses USX surface classes from usx-standard.css.
 * @category surfaces
 * @usage Routed at '{{cookiecutter.route_path}}'
 */
import { ref } from 'vue'
import { use{{cookiecutter.surface_id|capitalize}}Store } from '../../stores/{{cookiecutter.surface_id}}'
import UInput from '../../skills/atoms/UInput.vue'
import UButton from '../../skills/atoms/UButton.vue'
import USpinner from '../../skills/atoms/USpinner.vue'

const store = use{{cookiecutter.surface_id|capitalize}}Store()
const input = ref('')
const messagesRef = ref<HTMLElement | null>(null)

function send() {
  if (!input.value.trim() || store.loading) return
  store.sendMessage(input.value)
  input.value = ''
}
</script>

<style scoped>
/* Surface-specific overrides only — layout handled by .surface__* classes */
</style>
