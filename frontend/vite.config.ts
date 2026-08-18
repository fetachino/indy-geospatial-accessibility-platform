import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
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
        functions: 10,
        statements: 40,
        branches: 35,
      },
    },
  },
});
