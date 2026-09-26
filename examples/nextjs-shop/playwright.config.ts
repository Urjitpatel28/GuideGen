import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  use: { baseURL: "http://localhost:3210" },
  webServer: { command: "npm run seed && npm run dev", url: "http://localhost:3210/login", reuseExistingServer: true, timeout: 180000 },
});
