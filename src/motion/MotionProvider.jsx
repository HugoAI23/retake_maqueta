import { createContext, useContext, useEffect, useState } from 'react'

const REDUCE_QUERY = '(prefers-reduced-motion: reduce)'

const MotionContext = createContext({ reducedMotion: false })

function readPreference() {
  return Boolean(globalThis.matchMedia?.(REDUCE_QUERY).matches)
}

/**
 * Expone si el usuario pide reducir movimiento en su sistema y reacciona si
 * cambia la preferencia (RF-88). Todas las animaciones del marco la consultan
 * a través de esta capa (plan D-12).
 *
 * @param {{ children: import('react').ReactNode, forceReducedMotion?: boolean }} props
 *   `forceReducedMotion` solo se usa en pruebas.
 */
export function MotionProvider({ children, forceReducedMotion }) {
  const [reducedMotion, setReducedMotion] = useState(readPreference)

  useEffect(() => {
    const media = globalThis.matchMedia?.(REDUCE_QUERY)
    if (!media) return undefined
    const onChange = () => setReducedMotion(media.matches)
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])

  const value = { reducedMotion: forceReducedMotion ?? reducedMotion }
  return <MotionContext.Provider value={value}>{children}</MotionContext.Provider>
}

/** @returns {boolean} `true` si hay que desactivar las animaciones (RF-88). */
export function useReducedMotion() {
  return useContext(MotionContext).reducedMotion
}
