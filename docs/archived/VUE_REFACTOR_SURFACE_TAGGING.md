# Vue Refactor — Surface Analysis & Tagging Framework

> **Date:** 2026-06-28  
> **Purpose:** Canonical inventory of every UI surface, tagged for migration priority, complexity, and target Vue architecture.  
> **Architecture:** "Skills-First" Vue 3 + Pinia + Vite + Composition API (`<script setup>`)

---

## Tagging Convention

Every surface/component is tagged with:

| Tag | Meaning |
|-----|---------|
| **P0** | Core shell — must exist for the app to function (router, layout, store) |
| **P1** | Primary user-facing surfaces — migrated in first pass |
| **P2** | Secondary surfaces — migrated after P1 stabilizes |
| **P3** | Specialized/nice-to-have — migrated last or deferred |
| **🔴 High** | High complexity: heavy state, canvas/WebSocket, custom rendering engine |
| **🟡 Medium** | Medium complexity: forms, API calls, standard UI patterns |
| **🟢 Low** | Low complexity: static content, simple display, iframe wrappers |
| **🧩 Atomic** | Becomes a reusable `<U*>` component in the Skills library |
| **🏛️ Organism** | Composes multiple atoms/molecules into a full surface |
| **📦 Store** | Requires a dedicated Pinia store |
| **🔌 API** | Has backend API integration |
| **🎨 USX** | Uses the USX design system (carries over as CSS custom properties) |

---

## 0. Foundation Layer (P0) — Build First

These are the Vue scaffolding pieces that must exist before any surface can be mounted.

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **App Shell / Router** | `main.tsx` (BrowserRouter + routes) | `src/router/index.ts` — Vue Router 4 with same route map | P0 🟡 Medium |
| **Root Layout** | `App.tsx` + `GlobalToolbar` + `SurfaceShellContext` | `src/layouts/AppShell.vue` — toolbar + router-view + snackbar host | P0 🟡 Medium 🏛️ Organism |
| **Pinia Store Setup** | Scattered Context/Zustand | `src/stores/` — centralized Pinia store registry | P0 🟢 Low 📦 Store |
| **Global Settings Store** | `useGlobalSettings.ts` (localStorage) | `stores/settings.ts` — Pinia + persisted state | P0 🟢 Low 📦 Store |
| **DevMode Store** | `useDevMode.tsx` (Context + polling) | `stores/devMode.ts` — Pinia + fetch probe | P0 🟢 Low 📦 Store 🔌 API |
| **Snackbar Store** | `useSurfaceStore.ts` | `stores/snackbar.ts` — Pinia with queue management | P0 🟢 Low 📦 Store |
| **USX Design Tokens** | `src/styles/usx/*.css` | `src/styles/usx/*.css` — CSS custom properties carry over unchanged | P0 🟢 Low 🎨 USX |
| **API Client Layer** | Scattered `fetch()` calls | `src/api/client.ts` — centralized fetch wrapper with base URL config | P0 🟡 Medium 🔌 API |
| **Skills Library Shell** | N/A (new) | `src/skills/` — atomic component library with JSDoc standards | P0 🟢 Low 🧩 Atomic |

---

## 1. Dashboard / Mission Control (P1)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **DashboardSurface** | `surfaces/dashboard/DashboardSurface.tsx` | `surfaces/DashboardSurface.vue` — surface hub with cards | P1 🟡 Medium 🏛️ Organism 🔌 API |
| **Surface Card Component** | Inline in DashboardSurface | `skills/molecules/SurfaceCard.vue` — reusable card for each surface | P1 🟢 Low 🧩 Atomic |
| **Surface Action Buttons** | Start/Stop/Restart/Repair/Debug | `skills/molecules/SurfaceActions.vue` — action button group | P1 🟢 Low 🧩 Atomic 🔌 API |
| **Starred Surfaces** | Favorites in DashboardSurface | `skills/molecules/StarredSurfaces.vue` | P1 🟢 Low 🧩 Atomic |

---

## 2. AssistUI — AI Chat (P1 🔴 High)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **AssistUISurface** | `surfaces/assistui/AssistUISurface.tsx` | `surfaces/AssistUISurface.vue` — full-page AI chat | P1 🔴 High 🏛️ Organism 🔌 API |
| **Chat Message Component** | Inline in AssistUI | `skills/molecules/ChatMessage.vue` — single message render | P1 🟡 Medium 🧩 Atomic |
| **Chat Input Bar** | Inline in AssistUI | `skills/molecules/ChatInput.vue` — textarea + send + model selector | P1 🟡 Medium 🧩 Atomic |
| **Model Selector** | Inline in AssistUI | `skills/atoms/ModelSelector.vue` — dropdown for LLM models | P1 🟢 Low 🧩 Atomic 🔌 API |
| **Agent Mode Switcher** | Vault/Developer/Agent modes | `skills/molecules/AgentModeSwitcher.vue` | P1 🟡 Medium 🧩 Atomic |
| **Prompt Cards** | Inline in AssistUI | `skills/molecules/PromptCard.vue` — clickable prompt suggestion | P1 🟢 Low 🧩 Atomic |
| **Floating Chat Panel** | `FloatingChatWrapper` | `components/FloatingChat.vue` — mini chat overlay on other surfaces | P1 🟡 Medium 🏛️ Organism |
| **Chat Store** | Local state in AssistUI | `stores/chat.ts` — Pinia: messages, streaming state, model, agent mode | P1 🔴 High 📦 Store 🔌 API |

---

## 3. Developer Surface (P1 🔴 High)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **DeveloperSurface** | `surfaces/developer/DeveloperSurface.tsx` | `surfaces/DeveloperSurface.vue` — tabbed dev lane | P1 🔴 High 🏛️ Organism |
| **Models Panel** | `surfaces/developer/panels/ModelsPanel.tsx` | `surfaces/developer/panels/ModelsPanel.vue` | P1 🟡 Medium 🔌 API |
| **Dev Agents Panel** | `surfaces/developer/panels/AgentsPanel.tsx` | `surfaces/developer/panels/DevAgentsPanel.vue` | P1 🟡 Medium 🔌 API |
| **Kanban Panel** | `components/KanbanBoard.tsx` | `skills/organisms/KanbanBoard.vue` — reusable kanban | P1 🔴 High 🧩 Atomic 📦 Store |
| **Repos Panel** | `surfaces/developer/panels/ReposPanel.tsx` | `surfaces/developer/panels/ReposPanel.vue` | P1 🟡 Medium 🔌 API |
| **Review Panel** | `surfaces/developer/panels/ReviewPanel.tsx` | `surfaces/developer/panels/ReviewPanel.vue` | P1 🟡 Medium 🔌 API |
| **Skills Panel** | `surfaces/developer/panels/SkillsPanel.tsx` | `surfaces/developer/panels/SkillsPanel.vue` | P1 🟡 Medium 🔌 API |
| **Workflows → Dev Flow** | `surfaces/developer/panels/WorkflowsPanel.tsx` | `surfaces/developer/panels/DevFlowPanel.vue` | P1 🟡 Medium 🔌 API |
| **Settings Panel** | `surfaces/developer/panels/SettingsPanel.tsx` | `surfaces/developer/panels/DevSettingsPanel.vue` | P1 🟢 Low |
| **Developer Store** | Local state per panel | `stores/developer.ts` — Pinia: active tab, panel state | P1 🟡 Medium 📦 Store |

---

## 4. Server / Operations Surface (P1 🟡 Medium)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **UServerSurface** | `surfaces/userver/UServerSurface.tsx` | `surfaces/ServerSurface.vue` — tabbed ops panel | P1 🟡 Medium 🏛️ Organism |
| **Services Panel** | Inline tabs | `surfaces/server/panels/ServicesPanel.vue` | P1 🟡 Medium 🔌 API |
| **Logs Panel** | Inline tabs | `surfaces/server/panels/LogsPanel.vue` | P1 🟡 Medium 🔌 API |
| **Runtime Agents Panel** | Inline tabs | `surfaces/server/panels/RuntimeAgentsPanel.vue` | P1 🟡 Medium 🔌 API |
| **Budget Panel** | Inline tabs | `surfaces/server/panels/BudgetPanel.vue` | P1 🟢 Low 🔌 API |
| **Snacks Panel** | Inline tabs | `surfaces/server/panels/SnacksPanel.vue` | P1 🟡 Medium 🔌 API |
| **Automation Workflows** | Inline tabs | `surfaces/server/panels/AutomationPanel.vue` | P1 🟡 Medium 🔌 API |
| **Server Store** | Local state | `stores/server.ts` — Pinia: services, logs, budget, agents | P1 🟡 Medium 📦 Store 🔌 API |

---

## 5. UCode / GridCore Surface (P2 🔴 High)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **UCodeSurface** | `surfaces/ucode/UCodeSurface.tsx` | `surfaces/UCodeSurface.vue` — GridCore dashboard + terminal | P2 🔴 High 🏛️ Organism |
| **GridCoreDashboard** | `surfaces/ucode/GridCoreDashboard.tsx` | `surfaces/ucode/GridCoreDashboard.vue` | P2 🔴 High 🏛️ Organism 🔌 API |
| **GridUI Panels** | `surfaces/gridui/panels/*` | `surfaces/ucode/panels/*` — Terminal, Teletext, Grid Editor, etc. | P2 🔴 High 🏛️ Organism |
| **Grid Algebra Engine** | `surfaces/gridui/grid-algebra/*` | `src/engines/grid-algebra/*` — pure TS, framework-agnostic | P2 🔴 High |
| **GridUI Store** | `GridUIStore.ts` (Context-based) | `stores/gridui.ts` — Pinia: panels, viewport, fonts, layers | P2 🔴 High 📦 Store |
| **GridCore Settings** | `useGridCoreSettings.ts` | `stores/gridcoreSettings.ts` — Pinia + persisted | P2 🟢 Low 📦 Store |

---

## 6. Workflow Surface (P2 🟡 Medium)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **WorkflowSurface** | `surfaces/workflow/WorkflowSurface.tsx` | `surfaces/WorkflowSurface.vue` — missions, tasks, binder, publish | P2 🟡 Medium 🏛️ Organism |
| **KanbanBoard** | `components/KanbanBoard.tsx` | `skills/organisms/KanbanBoard.vue` — shared with Developer | P2 🔴 High 🧩 Atomic 📦 Store |
| **TaskDetailDrawer** | `components/TaskDetailDrawer.tsx` | `skills/molecules/TaskDetailDrawer.vue` | P2 🟡 Medium 🧩 Atomic |
| **Binder Panel** | Inline in WorkflowSurface | `surfaces/workflow/panels/BinderPanel.vue` — file drop compiler | P2 🟡 Medium 🧩 Atomic |
| **Missions Panel** | Inline in WorkflowSurface | `surfaces/workflow/panels/MissionsPanel.vue` | P2 🟢 Low 🔌 API |
| **Workflow Store** | Local state | `stores/workflow.ts` — Pinia: tasks, missions, binder state | P2 🟡 Medium 📦 Store 🔌 API |

---

## 7. System / Admin Surface (P2 🟡 Medium)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **USystemSurface** | `surfaces/system/USystemSurface.tsx` | `surfaces/SystemSurface.vue` — pages, tools, services, settings | P2 🟡 Medium 🏛️ Organism |
| **SystemToolsSurface** | `surfaces/systemtools/SystemToolsSurface.tsx` | Merged into SystemSurface | P2 🟡 Medium |
| **S-Page Registry** | `src/pages/spage-registry.ts` | `src/pages/spage-registry.ts` — carries over (TS, framework-agnostic) | P2 🟢 Low |
| **S100 Tool Builder** | `src/pages/S100ToolBuilder.tsx` | `pages/S100ToolBuilder.vue` | P2 🟡 Medium |
| **S101 Story Builder** | `src/pages/S101StoryBuilder.tsx` | `pages/S101StoryBuilder.vue` | P2 🟡 Medium |
| **S300 Workflow Builder** | `src/pages/S300WorkflowBuilder.tsx` | `pages/S300WorkflowBuilder.vue` | P2 🟡 Medium 🔌 API |
| **S310 Clipboard Orchestration** | `src/pages/S310ClipboardOrchestration.tsx` | `pages/S310ClipboardOrchestration.vue` | P2 🟡 Medium 🔌 API |
| **S320 Knowledge Tools** | `src/pages/S320KnowledgeTools.tsx` | `pages/S320KnowledgeTools.vue` | P2 🟡 Medium 🔌 API |
| **S330 Migration Dashboard** | `src/pages/S330MigrationDashboard.tsx` | `pages/S330MigrationDashboard.vue` | P2 🟡 Medium 🔌 API |
| **S600 Learning Hub** | `src/pages/S600Learning.tsx` | `pages/S600Learning.vue` | P2 🟢 Low |
| **System Store** | Local state | `stores/system.ts` — Pinia: active page, tool registry | P2 🟢 Low 📦 Store |

---

## 8. SnackMachine Surface (P2 🟡 Medium)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **SnackMachineSurface** | `surfaces/snackmachine/SnackMachineSurface.tsx` | `surfaces/SnackMachineSurface.vue` — snack/MCP/vault scheduler | P2 🟡 Medium 🏛️ Organism 🔌 API |
| **SnackMachine Store** | Local state | `stores/snackMachine.ts` — Pinia: scheduler, MCP status, vault sync | P2 🟡 Medium 📦 Store 🔌 API |

---

## 9. BrowserUI Surface (P3 🟡 Medium)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **BrowserUISurface** | `surfaces/browserui/BrowserUISurface.tsx` | `surfaces/BrowserUISurface.vue` — web reader with bookmark stacks | P3 🟡 Medium 🏛️ Organism |
| **Bookmark Stack Cards** | Kanban-style card stacks | `skills/molecules/BookmarkStack.vue` | P3 🟢 Low 🧩 Atomic |

---

## 10. Documentation Surface (P3 🟢 Low)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **DocumentationSurface** | `surfaces/documentation/DocumentationSurface.tsx` | `surfaces/DocumentationSurface.vue` — learning hub + iframe docs | P3 🟢 Low 🏛️ Organism |

---

## 11. Standalone Surfaces (P3)

| Item | React Source | Vue Target | Tags |
|------|-------------|------------|------|
| **TeletextSurface** | `surfaces/teletext/TeletextSurface.tsx` | `surfaces/TeletextSurface.vue` — Ceefax viewer (BBCSDL) | P3 🔴 High 🏛️ Organism |
| **TerminalSurface** | `surfaces/terminal/TerminalSurface.tsx` | `surfaces/TerminalSurface.vue` — BBC BASIC terminal (BBCSDL) | P3 🔴 High 🏛️ Organism |

---

## 12. Shared Components → Skills Library

These are the reusable "Skills" that get extracted into the atomic component library.

### Atoms (`src/skills/atoms/`)

| Component | React Source | Vue Target | Tags |
|-----------|-------------|------------|------|
| **UButton** | Various `<button>` patterns | `skills/atoms/UButton.vue` | 🧩 Atomic 🟢 Low |
| **UInput** | Various `<input>` patterns | `skills/atoms/UInput.vue` | 🧩 Atomic 🟢 Low |
| **UIcon** | `components/Icon.tsx` | `skills/atoms/UIcon.vue` | 🧩 Atomic 🟢 Low |
| **ModelSelector** | Inline in AssistUI | `skills/atoms/ModelSelector.vue` | 🧩 Atomic 🟢 Low |
| **Badge/Tag** | Various status badges | `skills/atoms/UBadge.vue` | 🧩 Atomic 🟢 Low |
| **Spinner/Loader** | Various loading states | `skills/atoms/USpinner.vue` | 🧩 Atomic 🟢 Low |

### Molecules (`src/skills/molecules/`)

| Component | React Source | Vue Target | Tags |
|-----------|-------------|------------|------|
| **USearchBar** | Search inputs across surfaces | `skills/molecules/USearchBar.vue` | 🧩 Atomic 🟢 Low |
| **UFilePicker** | `components/FilepickerSidebar.tsx` | `skills/molecules/UFilePicker.vue` | 🧩 Atomic 🟡 Medium |
| **VaultSidebar** | `components/VaultSidebar.tsx` | `skills/molecules/VaultSidebar.vue` | 🧩 Atomic 🟡 Medium |
| **WorkspaceFilter** | `components/WorkspaceFilter.tsx` | `skills/molecules/WorkspaceFilter.vue` | 🧩 Atomic 🟢 Low |
| **BinderMissionFilter** | `components/BinderMissionFilter.tsx` | `skills/molecules/BinderMissionFilter.vue` | 🧩 Atomic 🟢 Low |
| **SurfaceCard** | Dashboard surface cards | `skills/molecules/SurfaceCard.vue` | 🧩 Atomic 🟢 Low |
| **SurfaceActions** | Start/Stop/Restart/Repair | `skills/molecules/SurfaceActions.vue` | 🧩 Atomic 🟢 Low |
| **ChatMessage** | AssistUI messages | `skills/molecules/ChatMessage.vue` | 🧩 Atomic 🟡 Medium |
| **ChatInput** | AssistUI input bar | `skills/molecules/ChatInput.vue` | 🧩 Atomic 🟡 Medium |
| **AgentModeSwitcher** | Vault/Developer/Agent | `skills/molecules/AgentModeSwitcher.vue` | 🧩 Atomic 🟡 Medium |
| **PromptCard** | AssistUI prompt suggestions | `skills/molecules/PromptCard.vue` | 🧩 Atomic 🟢 Low |
| **TaskDetailDrawer** | `components/TaskDetailDrawer.tsx` | `skills/molecules/TaskDetailDrawer.vue` | 🧩 Atomic 🟡 Medium |
| **BookmarkStack** | BrowserUI card stacks | `skills/molecules/BookmarkStack.vue` | 🧩 Atomic 🟢 Low |
| **DataTable** | `components/DataTable.tsx` | `skills/molecules/DataTable.vue` | 🧩 Atomic 🟡 Medium |
| **Tabs** | `components/Tabs/*` | `skills/molecules/UTabs.vue` | 🧩 Atomic 🟢 Low |

### Organisms (`src/skills/organisms/`)

| Component | React Source | Vue Target | Tags |
|-----------|-------------|------------|------|
| **UKanbanBoard** | `components/KanbanBoard.tsx` | `skills/organisms/UKanbanBoard.vue` | 🧩 Atomic 🔴 High 📦 Store |
| **GlobalToolbar** | `components/GlobalToolbar.tsx` | `skills/organisms/GlobalToolbar.vue` | 🧩 Atomic 🟡 Medium |
| **DiffEditor** | `components/DiffEditor.tsx` | `skills/organisms/UDiffEditor.vue` (CodeMirror 6) | 🧩 Atomic 🔴 High |
| **EditorView** | `components/EditorView.tsx` | `skills/organisms/UEditorView.vue` (CodeMirror 6) | 🧩 Atomic 🔴 High |
| **StoryView** | `components/StoryView.tsx` | `skills/organisms/UStoryView.vue` | 🧩 Atomic 🟡 Medium |
| **MarpSlide** | `components/MarpSlide.tsx` | `skills/organisms/UMarpSlide.vue` | 🧩 Atomic 🟡 Medium |

---

## 13. Pinia Stores — Complete List

| Store | Source | Purpose | Surfaces Using It |
|-------|--------|---------|-------------------|
| `stores/settings.ts` | `useGlobalSettings.ts` | Font, size, palette, light/dark | Global |
| `stores/devMode.ts` | `useDevMode.tsx` | Dev server probe, toggle | Developer, AppShell |
| `stores/snackbar.ts` | `useSurfaceStore.ts` | Notification queue | Global |
| `stores/shell.ts` | `SurfaceShellContext.tsx` | Sidebar open, chat open, last surface | Global |
| `stores/chat.ts` | AssistUI local state | Messages, streaming, model, agent mode | AssistUI |
| `stores/developer.ts` | Developer local state | Active tab, panel state | Developer |
| `stores/server.ts` | Server local state | Services, logs, budget, agents | Server |
| `stores/gridui.ts` | `GridUIStore.ts` | Panels, viewport, fonts, layers | UCode, GridUI |
| `stores/gridcoreSettings.ts` | `useGridCoreSettings.ts` | GridCore-specific settings | UCode |
| `stores/workflow.ts` | Workflow local state | Tasks, missions, binder | Workflow |
| `stores/system.ts` | System local state | Active page, tool registry | System |
| `stores/snackMachine.ts` | SnackMachine local state | Scheduler, MCP, vault sync | SnackMachine |

---

## 14. Migration Wave Plan

### Wave 0: Foundation (Week 1)
- [ ] Scaffold Vue 3 + Vite + Pinia project
- [ ] Set up Vue Router with all routes
- [ ] Build AppShell layout (toolbar + router-view + snackbar)
- [ ] Create API client layer (`src/api/client.ts`)
- [ ] Port USX CSS custom properties
- [ ] Create Skills library shell with JSDoc standards
- [ ] Build atoms: UButton, UInput, UIcon, UBadge, USpinner
- [ ] Create stores: settings, devMode, snackbar, shell

### Wave 1: Core Surfaces (Week 2-3)
- [ ] DashboardSurface (Mission Control)
- [ ] AssistUISurface (AI Chat) — highest complexity
- [ ] DeveloperSurface (Dev Lane)
- [ ] ServerSurface (Operations)
- [ ] Shared molecules: SurfaceCard, SurfaceActions, ChatMessage, ChatInput, etc.

### Wave 2: Secondary Surfaces (Week 4-5)
- [ ] WorkflowSurface (Missions, Tasks, Binder)
- [ ] SystemSurface (Admin, S-Pages)
- [ ] SnackMachineSurface
- [ ] UCodeSurface (GridCore + Terminal)

### Wave 3: Specialized Surfaces (Week 6+)
- [ ] BrowserUISurface
- [ ] DocumentationSurface
- [ ] TeletextSurface
- [ ] TerminalSurface

### Wave 4: Polish & Optimization
- [ ] Performance audit (lazy loading, code splitting)
- [ ] Vitest unit tests for all Skills
- [ ] Storybook documentation for Skills library
- [ ] Accessibility audit
- [ ] Remove all React dependencies

---

## 15. Key Architectural Decisions

### ✅ What Carries Over (Framework-Agnostic)
- **USX Design System** — CSS custom properties, no JS dependency
- **Grid Algebra Engine** — pure TypeScript, no React
- **S-Page Registry** — pure TypeScript mapping
- **API endpoint contracts** — backend unchanged
- **CodeMirror 6** — works with Vue (different binding layer)

### ❌ What Gets Replaced
- React Router → **Vue Router 4**
- React Context/Zustand → **Pinia**
- `fetch()` scattered → **Centralized API client**
- MUI Icons → **Iconify** (framework-agnostic, tree-shakeable)
- Emotion styled → **Scoped `<style>` + CSS custom properties**
- Pico CSS → **Keep Pico CSS** (classless, works with Vue)

### 🆕 What's New
- **Skills Library** — atomic component library with JSDoc
- **Pinia stores** — standardized state management
- **Vite HMR** — instant dev feedback
- **`<script setup>`** — consistent component structure
- **Vitest** — unit testing
- **Storybook** — component documentation

---

## 16. Component JSDoc Standard

Every Skill component follows this template:

```vue
<template>
  <!-- Template here -->
</setup>

<script setup lang="ts">
/**
 * @component UButton
 * @description Primary action button with variant support.
 * @category atoms
 * @props {string} variant - 'primary' | 'secondary' | 'ghost'
 * @props {string} size - 'sm' | 'md' | 'lg'
 * @props {boolean} disabled - Disables the button
 * @emits {MouseEvent} click - Fires on button click
 * @usage <UButton variant="primary" size="md">Submit</UButton>
 */
interface Props {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
})

const emit =defineEmits<{
  click: [event: MouseEvent]
}>()
</script>
```

---

*This document is the single source of truth for the Vue refactor. Update it as surfaces are migrated.*
