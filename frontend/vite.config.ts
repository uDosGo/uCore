import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import path from "path"

// Port is managed exclusively by Snackbar — Vite just binds to whatever port is given.
const PORT = parseInt(process.env.VITE_PORT || "5173", 10)

// Resolve ~/Code/ repo roots for cross-repo @aliases
// __dirname = uConnect/ui/ → ../.. = ~/Code/
const CODE_ROOT = path.resolve(__dirname, "../..")

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Local src alias
      "@": path.resolve(__dirname, "src"),
      // Cross-repo aliases (resolve to ~/Code/<repo>)
      "@uCode3": path.resolve(CODE_ROOT, "uCode3"),
      "@HomeNest": path.resolve(CODE_ROOT, "uConnect/homenest-console"),
      "@usxd-browser": path.resolve(CODE_ROOT, "uConnect/usxd-browser"),
      // @usx-pkg avoids conflict with @usx/styles npm package (symlinked in node_modules)
      "@usx-pkg": path.resolve(CODE_ROOT, "uConnect/packages/usx"),
    },
  },
  server: {
    port: PORT,
    strictPort: true,
    host: "localhost",
    fs: {
      allow: [".."],
    },
    hmr: {
      host: "localhost",
    },
  },
})
