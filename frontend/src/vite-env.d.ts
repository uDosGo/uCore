/* ═══════════════════════════════════════════════════════════════════
   vite-env.d.ts — Vite + CSS Module Type Declarations
   ═══════════════════════════════════════════════════════════════════
   Provides TypeScript with type information for:
   - CSS/SCSS module imports (side-effect imports)
   - @usx/styles/* subpath imports (CSS-only packages)
   - react-router-dom (used in main.tsx routing)
   ═══════════════════════════════════════════════════════════════════ */

/// <reference types="vite/client" />

/* ─── CSS Module Declarations ───────────────────────────────────── */
declare module '*.css' {
  const content: string
  export default content
}

declare module '*.scss' {
  const content: string
  export default content
}

declare module '*.less' {
  const content: string
  export default content
}

/* ─── @usx/styles Subpath Imports ───────────────────────────────── */
declare module '@usx/styles' {
  const content: string
  export default content
}

declare module '@usx/styles/tokens' {
  const content: string
  export default content
}

declare module '@usx/styles/tokens/*' {
  const content: string
  export default content
}

declare module '@usx/styles/palettes' {
  const content: string
  export default content
}

declare module '@usx/styles/components/*' {
  const content: string
  export default content
}

declare module '@usx/styles/react' {
  export { USXThemeProvider, useUSXTheme } from '@usx/styles/react/theme'
}

declare module '@usx/styles/react/icon' {
  export { Icon } from '@usx/styles/react/icon'
}

declare module '@usx/styles/react/surface-snackbar' {
  export { SurfaceSnackbar } from '@usx/styles/react/surface-snackbar'
}

declare module '@usx/styles/react/surface-store' {
  export { useSurfaceStore } from '@usx/styles/react/surface-store'
}

/* ─── react-router-dom ──────────────────────────────────────────── */
declare module 'react-router-dom' {
  import React from 'react'

  interface RouteProps {
    path?: string
    element?: React.ReactNode
    children?: React.ReactNode
    index?: boolean
  }

  interface BrowserRouterProps {
    children?: React.ReactNode
    basename?: string
  }

  interface MemoryRouterProps {
    children?: React.ReactNode
    initialEntries?: string[]
    initialIndex?: number
  }

  interface NavigateProps {
    to: string
    replace?: boolean
    state?: Record<string, unknown>
  }

  interface OutletProps {
    context?: unknown
  }

  export const BrowserRouter: React.FC<BrowserRouterProps>
  export const MemoryRouter: React.FC<MemoryRouterProps>
  export const Routes: React.FC<{ children?: React.ReactNode }>
  export const Route: React.FC<RouteProps>
  export const Navigate: React.FC<NavigateProps>
  export const Outlet: React.FC<OutletProps>
  export const useNavigate: () => (path: string, options?: { replace?: boolean; state?: Record<string, unknown> }) => void
  export const useLocation: () => { pathname: string; search: string; hash: string; state: unknown }
  export const useParams: () => Record<string, string | undefined>
  export const Link: React.FC<{ to: string; children?: React.ReactNode; className?: string; onClick?: React.MouseEventHandler; style?: React.CSSProperties }>
  export const NavLink: React.FC<{ to: string; children?: React.ReactNode; className?: string | ((props: { isActive: boolean }) => string); style?: React.CSSProperties | ((props: { isActive: boolean }) => React.CSSProperties) }>
}

/* ─── bootstrap-icons ───────────────────────────────────────────── */
declare module 'bootstrap-icons/font/bootstrap-icons.css' {
  const content: string
  export default content
}
