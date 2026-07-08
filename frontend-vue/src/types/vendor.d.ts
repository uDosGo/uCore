/**
 * @module types/vendor
 * @description Type declarations for vendored libraries that ship their own types.
 */
declare module '@vendor/md-editor' {
  import type { DefineComponent } from 'vue'

  export const MdEditor: DefineComponent<any, any, any>
  export const MdPreview: DefineComponent<any, any, any>
  export const MdCatalog: DefineComponent<any, any, any>
  export const MdModal: DefineComponent<any, any, any>
}

declare module '@vendor/md-editor-style' {
  const style: string
  export default style
}

declare module '@vendor/md-editor-preview' {
  const style: string
  export default style
}

declare module '@udos/usx-tokens' {
  const _: any
  export default _
}

declare module '@udos/usx-tokens/*' {
  const _: any
  export default _
}
