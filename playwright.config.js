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
    // Spec 003: la API, para el canal de eventos a través del proxy de Vite (T-061, T-082). Las
    // demás pruebas simulan sus respuestas en el navegador y no dependen de ninguna base de datos.
    {
      command: 'uv run --directory backend uvicorn app.main:app --port 8000',
      url: 'http://localhost:8000/api/health',
      reuseExistingServer: true,
    },
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
