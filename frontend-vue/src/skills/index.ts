/**
 * @module skills
 * @description Central Skills registry — the "Skills-First" component library.
 *
 * Every reusable UI component is registered here with:
 * - Component reference
 * - Category (atom / molecule / organism)
 * - JSDoc metadata for AI agent discovery
 *
 * AI agents can query this registry to discover available Skills
 * and their props/emits before generating code.
 */

// ─── Atoms ─────────────────────────────────────────────────────────
export { default as UButton } from './atoms/UButton.vue'
export { default as UInput } from './atoms/UInput.vue'
export { default as UIcon } from './atoms/UIcon.vue'
export { default as UBadge } from './atoms/UBadge.vue'
export { default as USpinner } from './atoms/USpinner.vue'

// ─── Molecules ─────────────────────────────────────────────────────
export { default as SurfaceCard } from './molecules/SurfaceCard.vue'
export { default as FilepickerSidebar } from './molecules/FilepickerSidebar.vue'
export { default as SnackbarHost } from './molecules/SnackbarHost.vue'
export { default as SurfaceTabNav } from './molecules/SurfaceTabNav.vue'
export { default as WorkspaceFilter } from './molecules/WorkspaceFilter.vue'
export { default as BinderMissionFilter } from './molecules/BinderMissionFilter.vue'

// ─── Editor Skills (vendored md-editor-v3) ─────────────────────────
export { MarkdownEditor, MarkdownPreview } from './molecules/editor'

// ─── Organisms ──────────────────────────────────────────────────────
export { default as EditorPanel } from './organisms/EditorPanel.vue'
export { default as GlobalToolbar } from './organisms/GlobalToolbar.vue'

// ─── Skill Metadata (for AI agent discovery) ───────────────────────
export interface SkillMeta {
  name: string
  category: 'atom' | 'molecule' | 'organism'
  description: string
  props: string[]
  emits: string[]
  path: string
}

export const skillRegistry: SkillMeta[] = [
  // Atoms
  { name: 'UButton', category: 'atom', description: 'Action button with variant/size/icon', props: ['variant', 'size', 'disabled', 'icon'], emits: ['click'], path: 'skills/atoms/UButton.vue' },
  { name: 'UInput', category: 'atom', description: 'Text input with icon support', props: ['modelValue', 'type', 'placeholder', 'disabled', 'icon'], emits: ['update:modelValue', 'enter'], path: 'skills/atoms/UInput.vue' },
  { name: 'UIcon', category: 'atom', description: 'Iconify icon wrapper', props: ['name', 'size', 'spin'], emits: [], path: 'skills/atoms/UIcon.vue' },
  { name: 'UBadge', category: 'atom', description: 'Status badge with semantic colors', props: ['type'], emits: [], path: 'skills/atoms/UBadge.vue' },
  { name: 'USpinner', category: 'atom', description: 'Loading spinner', props: ['size'], emits: [], path: 'skills/atoms/USpinner.vue' },
  // Molecules
  { name: 'SurfaceCard', category: 'molecule', description: 'Dashboard surface card', props: ['surface'], emits: ['click'], path: 'skills/molecules/SurfaceCard.vue' },
  { name: 'FilepickerSidebar', category: 'molecule', description: 'Unified file browser sidebar with vault layer filters, binder/mission filter, search, file type icons, and new file action', props: ['open', 'compact'], emits: ['fileSelect', 'newFile'], path: 'skills/molecules/FilepickerSidebar.vue' },
  { name: 'SnackbarHost', category: 'molecule', description: 'Global notification host', props: [], emits: [], path: 'skills/molecules/SnackbarHost.vue' },
  { name: 'SurfaceTabNav', category: 'molecule', description: 'Reusable tab navigation bar with horizontal/vertical orientation toggle', props: ['tabs', 'modelValue', 'orientation', 'showToggle'], emits: ['update:modelValue', 'toggle-orientation'], path: 'skills/molecules/SurfaceTabNav.vue' },
  { name: 'WorkspaceFilter', category: 'molecule', description: 'Workspace selector filter', props: [], emits: [], path: 'skills/molecules/WorkspaceFilter.vue' },
  { name: 'BinderMissionFilter', category: 'molecule', description: 'Binder/mission selector filter', props: [], emits: [], path: 'skills/molecules/BinderMissionFilter.vue' },
  { name: 'MarkdownEditor', category: 'molecule', description: 'Full markdown editor (md-editor-v3 vendored)', props: ['modelValue', 'toolbars', 'preview', 'htmlPreview', 'noUpload', 'autofocus'], emits: ['update:modelValue', 'save', 'change'], path: 'skills/molecules/editor/MarkdownEditor.vue' },
  { name: 'MarkdownPreview', category: 'molecule', description: 'Read-only markdown renderer', props: ['content', 'previewId'], emits: [], path: 'skills/molecules/editor/MarkdownPreview.vue' },
  // Organisms
  { name: 'GlobalToolbar', category: 'organism', description: 'Top toolbar with nav, tabs, actions', props: ['tabs', 'chatMode', 'sidebarOpen'], emits: ['toggle-chat', 'toggle-sidebar'], path: 'skills/organisms/GlobalToolbar.vue' },
]
