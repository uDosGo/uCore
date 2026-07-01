/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '@marp-team/marp-core' {
  export class Marp {
    constructor(options?: any)
    render(markdown: string): { html: string; css: string }
  }
}
