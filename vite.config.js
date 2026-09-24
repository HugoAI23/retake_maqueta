import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// Configuración de Vite: React + Tailwind CSS.
// El bloque `test` lo lee Vitest (pruebas unitarias y de componentes).

// Proxy de /api al backend. `changeOrigin: false` conserva el `Host` del navegador: la página de
// administración solo acepta peticiones del mismo origen (spec 003, plan D-11), y con la forma
// abreviada ('/api': 'http://…') Vite reescribe el `Host` y el backend las rechaza con 403.
// `RETAKE_API_TARGET` permite apuntar a otro backend (por ejemplo, uno simulado en otra base de datos
// para la guía de verificación de la 003); sin ella, el de siempre.
const apiProxy = { '/api': { target: process.env.RETAKE_API_TARGET ?? 'http://localhost:8000', changeOrigin: false } }

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // En desarrollo, las llamadas a /api van al backend de FastAPI (spec 002, plan D-11):
  // el frontend usa /api como si fuera su propio origen, sin configurar CORS.
  server: {
    proxy: apiProxy,
  },
  // La versión compilada que se sirve con `vite preview` usa la misma API (spec 003, T-082).
  preview: {
    proxy: apiProxy,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    include: ['src/**/*.test.{js,jsx}'],
  },
})
