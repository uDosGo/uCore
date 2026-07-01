/**
 * uCore Vue — Entry Point
 * Skills-First Vue 3 + Pinia + Vite Architecture
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import { router } from './router'

// External dependencies are already loaded in index.html

// USX Design System - Import in correct order
import './styles/themes/base.css'
import './styles/themes/dark.css'
import './styles/usx-standard.css'

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)
app.mount('#app')
