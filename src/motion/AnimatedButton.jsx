import { animate } from 'animejs'
import { useRef } from 'react'
import { motionPresets } from './motionPresets.js'
import { useReducedMotion } from './MotionProvider.jsx'

/**
 * Botón del marco común con hover animado por Anime.js (RF-86, plan D-11).
 * El cambio de color del hover lo pone la clase CSS (RF-75); Anime.js solo
 * añade un ligero aumento de escala. Sin animación con reducir movimiento (RF-88).
 *
 * @param {import('react').ButtonHTMLAttributes<HTMLButtonElement> & { ref?: import('react').Ref<HTMLButtonElement> }} props
 */
export function AnimatedButton({ ref, onPointerEnter, onPointerLeave, ...props }) {
  const ownRef = useRef(null)
  const reducedMotion = useReducedMotion()

  const setRefs = (node) => {
    ownRef.current = node
    if (typeof ref === 'function') ref(node)
    else if (ref) ref.current = node
  }

  const scaleTo = (value) => {
    if (reducedMotion || !ownRef.current) return
    animate(ownRef.current, { scale: value, ...motionPresets.hover })
  }

  return (
    <button
      ref={setRefs}
      onPointerEnter={(event) => {
        scaleTo(1.05)
        onPointerEnter?.(event)
      }}
      onPointerLeave={(event) => {
        scaleTo(1)
        onPointerLeave?.(event)
      }}
      {...props}
    />
  )
}
