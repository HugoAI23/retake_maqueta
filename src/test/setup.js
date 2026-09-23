import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

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

afterEach(() => {
  cleanup()
  localStorage.clear()
  document.body.style.overflow = ''
})
