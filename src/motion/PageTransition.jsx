import { animate } from 'animejs'
import { createContext, useContext, useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router'
import { motionPresets } from './motionPresets.js'
import { useReducedMotion } from './MotionProvider.jsx'

/** Margen tras la duración de la transición por si la animación no llega a avisar. */
const FALLBACK_MARGIN_MS = 50

/** Si terminó la transición de la página actual; fuera de PageTransition, sí. */
const TransitionDoneContext = createContext(true)

/**
 * Transición de la zona de contenido al cambiar de página (RF-85): la página
 * nueva aparece con un fundido y un leve desplazamiento vertical en 200 ms
 * (RF-87). No se anima la primera carga ni con reducir movimiento (RF-88).
 *
 * Solo se anima cuando cambia la dirección respecto a la última vista. Así la
 * primera carga tampoco se anima en desarrollo, donde StrictMode monta los
 * efectos dos veces (fallo corregido; plan de la spec 002, I-32).
 *
 * Avisa a la página de cuándo termina la transición (spec 004, RF-28a; plan D-4):
 * la entrada de una tabla empieza después. Sin transición, avisa al momento.
 *
 * @param {{ children: import('react').ReactNode }} props
 */
export function PageTransition({ children }) {
  const { pathname } = useLocation()
  const reducedMotion = useReducedMotion()
  const ref = useRef(null)
  const lastPathname = useRef(pathname)
  // Última dirección cuya transición terminó. Se compara al pintar, así que la página
  // nueva ya sabe en su primer pintado que la transición no ha terminado.
  const [settledPathname, setSettledPathname] = useState(pathname)

  useEffect(() => {
    const changed = lastPathname.current !== pathname
    lastPathname.current = pathname
    const settle = () => setSettledPathname(pathname)
    if (!changed || reducedMotion || !ref.current) {
      settle()
      return undefined
    }
    const animation = animate(ref.current, {
      opacity: [0, 1],
      translateY: [8, 0],
      ...motionPresets.pageEnter,
      onComplete: settle,
    })
    const fallback = setTimeout(settle, motionPresets.pageEnter.duration + FALLBACK_MARGIN_MS)
    return () => {
      clearTimeout(fallback)
      animation.revert()
    }
  }, [pathname, reducedMotion])

  const done = reducedMotion || settledPathname === pathname

  return (
    <TransitionDoneContext.Provider value={done}>
      <div ref={ref} data-testid="page-transition">
        {children}
      </div>
    </TransitionDoneContext.Provider>
  )
}

/**
 * Si ya terminó la transición entre páginas (spec 004, RF-28a). La entrada de una
 * tabla espera a que valga `true`.
 * @returns {boolean}
 */
export function usePageTransitionDone() {
  return useContext(TransitionDoneContext)
}
