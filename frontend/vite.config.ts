import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  // MapLibre ships a browser worker that Vite's dependency optimizer can
  // incorrectly pre-bundle on Windows, leaving a missing worker module and a
  // blank map canvas. Keep the package unbundled for local development.
  optimizeDeps: {
    exclude: ["maplibre-gl"],
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text"],
      include: ["src/App.tsx"],
      thresholds: {
        // MapLibre/browser-only branches are not executable in jsdom; keep a
        // meaningful floor while interaction tests cover the rendered shell.
        lines: 40,
        functions: 9,
        statements: 40,
        branches: 35,
      },
    },
  },
});
