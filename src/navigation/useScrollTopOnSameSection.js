import { animate } from 'animejs'
import { useCallback } from 'react'
import { useLocation } from 'react-router'
import { motionPresets } from '../motion/motionPresets.js'
import { useReducedMotion } from '../motion/MotionProvider.jsx'

/**
 * Pulsar la entrada de la sección en la que ya se está lleva al principio de
 * la página (RF-15), sin crear una entrada nueva en el historial.
 *
 * El desplazamiento dura 300 ms como máximo (RF-87) y es instantáneo si el
 * usuario pide reducir movimiento (RF-88).
 *
 * @returns {(event: import('react').MouseEvent, path: string) => void}
 */
export function useScrollTopOnSameSection() {
  const { pathname } = useLocation()
  const reducedMotion = useReducedMotion()

  return useCallback(
    (event, path) => {
      if (path !== pathname) return
      event.preventDefault()
      if (reducedMotion || window.scrollY === 0) {
        window.scrollTo(0, 0)
        return
      }
      const position = { y: window.scrollY }
      animate(position, {
        y: 0,
        ...motionPresets.scrollTop,
        onUpdate: () => window.scrollTo(0, position.y),
      })
    },
    [pathname, reducedMotion],
  )
}
