import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  css: {
    transformer: "lightningcss"
  },
  resolve: {
    dedupe: ["react", "react-dom"]
  },
  server: {
    port: 5173
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
    coverage: {
      provider: "v8",
      include: ["src/services/**", "src/components/ProtectedRoute.tsx"]
    }
  }
});
