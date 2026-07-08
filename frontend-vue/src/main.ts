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
// Core tokens come from the shared @udos/usx-tokens package
import './styles/base.css' // local: wraps package tokens + PicoCSS mappings
import './styles/themes/dark.css' // uCore-specific themes
import '@udos/usx-tokens/themes/light.css' // light theme from package
import '@udos/usx-tokens' // usx-standard.css from package
import './styles/usx-extensions.css' // uCore-specific extensions: toolbar, multi-column, dev toggle

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)
app.mount('#app')
