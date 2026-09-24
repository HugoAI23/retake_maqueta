import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

// jsdom no implementa matchMedia: se simula con coincidencia falsa por defecto.
// Las pruebas que necesitan otro valor lo sustituyen con vi.spyOn / stubGlobal.
if (!window.matchMedia) {
  window.matchMedia = vi.fn((query) => ({
    matches: false,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
  }))
}

// jsdom tampoco implementa scrollTo.
window.scrollTo = vi.fn()

// Ninguna prueba sale a la red: por defecto, cualquier petición falla. Las pruebas que
// necesitan respuestas las simulan con vi.stubGlobal('fetch', ...). jsdom no tiene EventSource,
// así que el canal de eventos de la spec 003 queda inerte.
beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('Sin red en las pruebas'))))
})

afterEach(() => {
  vi.unstubAllGlobals()
  cleanup()
  localStorage.clear()
  document.body.style.overflow = ''
})
