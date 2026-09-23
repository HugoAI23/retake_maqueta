import { MAX_ANIMATION_MS } from '../config/layoutConstants.js'

/**
 * Duraciones y curvas comunes de las animaciones del marco (RF-87).
 * Ninguna puede superar MAX_ANIMATION_MS (lo comprueba motionPresets.test.js).
 */
export const motionPresets = {
  /** Entrada y salida del panel de navegación (RF-84). */
  panelSlide: { duration: 250, ease: 'outQuad' },
  /** Transición entre páginas (RF-85). */
  pageEnter: { duration: 200, ease: 'outQuad' },
  /** Hover de los botones (RF-86). */
  hover: { duration: 150, ease: 'outQuad' },
  /** Vuelta al principio de la página al pulsar la sección actual (RF-15). */
  scrollTop: { duration: 300, ease: 'inOutQuad' },
}

export { MAX_ANIMATION_MS }
