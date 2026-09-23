import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// Configuración de Vite: React + Tailwind CSS.
// El bloque `test` lo lee Vitest (pruebas unitarias y de componentes).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // En desarrollo, las llamadas a /api van al backend de FastAPI (spec 002, plan D-11):
  // el frontend usa /api como si fuera su propio origen, sin configurar CORS.
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    include: ['src/**/*.test.{js,jsx}'],
  },
})
