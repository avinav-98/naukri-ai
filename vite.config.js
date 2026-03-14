import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const rootDir = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react()],
  root: resolve(rootDir, "frontend/app"),
  build: {
    outDir: resolve(rootDir, "frontend/dist"),
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://127.0.0.1:8000",
      "/api": "http://127.0.0.1:8000",
    },
  },
});
