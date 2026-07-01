/**
 * @module router
 * @description Vue Router 4 — canonical surface routes.
 * Mirrors the React Router config from the legacy frontend.
 * Enhanced with Dev Mode guard that watches for toggle changes.
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useDevModeStore } from '../stores/devMode'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../surfaces/dashboard/DashboardSurface.vue'),
    meta: { title: 'Mission Control', icon: 'home' },
  },
  {
    path: '/assistui/:pathMatch(.*)*',
    name: 'assistui',
    component: () => import('../surfaces/assistui/AssistUISurface.vue'),
    meta: { title: 'AssistUI', icon: 'bolt' },
  },
  {
    path: '/ucode/:pathMatch(.*)*',
    name: 'ucode',
    component: () => import('../surfaces/ucode/UCodeSurface.vue'),
    meta: { title: 'uCode', icon: 'grid' },
  },
  {
    path: '/server/:pathMatch(.*)*',
    name: 'server',
    component: () => import('../surfaces/server/ServerSurface.vue'),
    meta: { title: 'Server', icon: 'server' },
  },
  {
    path: '/developer/:pathMatch(.*)*',
    name: 'developer',
    component: () => import('../surfaces/developer/DeveloperSurface.vue'),
    meta: { title: 'Developer', icon: 'code', devOnly: true },
  },
  {
    path: '/workflow/:pathMatch(.*)*',
    name: 'workflow',
    component: () => import('../surfaces/workflow/WorkflowSurface.vue'),
    meta: { title: 'Workflow', icon: 'workflow' },
  },
  {
    path: '/system/:pathMatch(.*)*',
    name: 'system',
    component: () => import('../surfaces/system/SystemSurface.vue'),
    meta: { title: 'System', icon: 'settings' },
  },
  {
    path: '/snackmachine/:pathMatch(.*)*',
    name: 'snackmachine',
    component: () => import('../surfaces/snackmachine/SnackMachineSurface.vue'),
    meta: { title: 'SnackMachine', icon: 'snack' },
  },
  {
    path: '/browserui/:pathMatch(.*)*',
    name: 'browserui',
    component: () => import('../surfaces/browserui/BrowserUISurface.vue'),
    meta: { title: 'Browser', icon: 'globe', hidden: true },
  },
  {
    path: '/documentation/:pathMatch(.*)*',
    name: 'documentation',
    component: () => import('../surfaces/documentation/DocumentationSurface.vue'),
    meta: { title: 'Documentation', icon: 'help' },
  },
  {
    path: '/teletext/:pathMatch(.*)*',
    name: 'teletext',
    component: () => import('../surfaces/teletext/TeletextSurface.vue'),
    meta: { title: 'Teletext', icon: 'tv' },
  },
  {
    path: '/terminal/:pathMatch(.*)*',
    name: 'terminal',
    component: () => import('../surfaces/terminal/TerminalSurface.vue'),
    meta: { title: 'Terminal', icon: 'terminal' },
  },
  // Legacy redirects
  {
    path: '/gridui/:pathMatch(.*)*',
    redirect: to => `/ucode${to.path.replace('/gridui', '')}`,
  },
  {
    path: '/userver/:pathMatch(.*)*',
    redirect: to => `/server${to.path.replace('/userver', '')}`,
  },
  // System pages (S-pages, P-pages)
  {
    path: '/:pathMatch(s\\d{3}|p\\d{3})',
    name: 'systempage',
    component: () => import('../surfaces/system/SystemPage.vue'),
    meta: { title: 'System Page' },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Dev mode guard — redirects to dashboard if Dev Mode is off
router.beforeEach(async (to) => {
  if (to.meta.devOnly) {
    const devMode = useDevModeStore()
    if (!devMode.probed) {
      await devMode.probe()
    }
    if (!devMode.showDevContent) {
      return { name: 'dashboard' }
    }
  }
})

// Update document title
router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} — uCore` : 'uCore'
})
