import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

const PORT = parseInt(process.env.VITE_PORT || '5175', 10)
const CODE_ROOT = path.resolve(__dirname, '../..')

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // Treat iconify-icon as a custom element (not a Vue component)
          isCustomElement: (tag) => tag === 'iconify-icon',
        },
      },
    }),
  ],
  resolve: {
    alias: {
      // Local src alias
      '@': path.resolve(__dirname, 'src'),
      // Vendored md-editor-v3
      '@vendor/md-editor': path.resolve(__dirname, 'src/vendor/md-editor-v3/lib/es/index.mjs'),
      '@vendor/md-editor-style': path.resolve(__dirname, 'src/vendor/md-editor-v3/lib/style.css'),
      '@vendor/md-editor-preview': path.resolve(__dirname, 'src/vendor/md-editor-v3/lib/preview.css'),
      // Cross-repo aliases (resolve to ~/Code/<repo>)
      '@uCode3': path.resolve(CODE_ROOT, 'uCode3'),
      '@HomeNest': path.resolve(CODE_ROOT, 'uConnect/homenest-console'),
      '@usxd-browser': path.resolve(CODE_ROOT, 'uConnect/usxd-browser'),
      '@usx-pkg': path.resolve(CODE_ROOT, 'uConnect/packages/usx'),
      '@udos/usx-tokens': path.resolve(__dirname, '../packages/usx-tokens'),
      '@udos/gridcore': path.resolve(CODE_ROOT, 'uCode/packages/gridcore/src/index.ts'),
      '@udos/viewport-renderer': path.resolve(CODE_ROOT, 'uCode/packages/viewport-renderer/src/index.ts'),
    },
  },
  server: {
    port: PORT,
    strictPort: true,
    host: 'localhost',
    fs: { allow: ['..'] },
    hmr: { host: 'localhost' },
    proxy: {
      '/snackmachine': {
        target: 'http://127.0.0.1:8484',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  // Ensure vendored .mjs files are handled correctly
  optimizeDeps: {
    exclude: ['@vendor/md-editor'],
  },
})
