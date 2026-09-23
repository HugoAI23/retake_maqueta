import { defineConfig, devices } from '@playwright/test'

// Pruebas de extremo a extremo (plan §6, decisión P-5).
// Dos entornos: desarrollo (incluye la página de demostración) y
// producción (versión compilada, donde la demostración no existe).
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  reporter: 'list',
  use: {
    ...devices['Desktop Chrome'],
    locale: 'es-ES',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'dev',
      testIgnore: /prod\//,
      use: { baseURL: 'http://localhost:5173' },
    },
    {
      name: 'prod',
      testIgnore: /dev\//,
      use: { baseURL: 'http://localhost:4173' },
    },
  ],
  webServer: [
    {
      command: 'npm run dev -- --port 5173 --strictPort',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
    },
    {
      command: 'npm run build && npm run preview -- --port 4173 --strictPort',
      url: 'http://localhost:4173',
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
})
