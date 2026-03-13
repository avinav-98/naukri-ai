import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [react()],
  root: resolve(__dirname, "frontend/app"),
  build: {
    outDir: resolve(__dirname, "frontend/dist"),
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/signin-google": "http://127.0.0.1:8000",
      "/logout": "http://127.0.0.1:8000",
    },
  },
});
