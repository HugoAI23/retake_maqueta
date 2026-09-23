import { animate } from 'animejs'
import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router'
import { motionPresets } from './motionPresets.js'
import { useReducedMotion } from './MotionProvider.jsx'

/**
 * Transición de la zona de contenido al cambiar de página (RF-85): la página
 * nueva aparece con un fundido y un leve desplazamiento vertical en 200 ms
 * (RF-87). No se anima la primera carga ni con reducir movimiento (RF-88).
 *
 * Solo se anima cuando cambia la dirección respecto a la última vista. Así la
 * primera carga tampoco se anima en desarrollo, donde StrictMode monta los
 * efectos dos veces (fallo corregido; plan de la spec 002, I-32).
 *
 * @param {{ children: import('react').ReactNode }} props
 */
export function PageTransition({ children }) {
  const { pathname } = useLocation()
  const reducedMotion = useReducedMotion()
  const ref = useRef(null)
  const lastPathname = useRef(pathname)

  useEffect(() => {
    const changed = lastPathname.current !== pathname
    lastPathname.current = pathname
    if (!changed || reducedMotion || !ref.current) return undefined
    const animation = animate(ref.current, {
      opacity: [0, 1],
      translateY: [8, 0],
      ...motionPresets.pageEnter,
    })
    return () => animation.revert()
  }, [pathname, reducedMotion])

  return (
    <div ref={ref} data-testid="page-transition">
      {children}
    </div>
  )
}
