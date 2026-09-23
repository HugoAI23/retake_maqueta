import { animate } from 'animejs'
import { useLayoutEffect, useState } from 'react'
import { motionPresets } from './motionPresets.js'
import { useReducedMotion } from './MotionProvider.jsx'

/**
 * Deslizamiento de entrada y salida del panel con Anime.js (RF-84).
 *
 * Al cerrar, el panel sigue en pantalla hasta que termina la animación de
 * salida; después se desmonta. Con reducir movimiento, aparece y desaparece
 * sin animación (RF-88).
 *
 * @param {boolean} isOpen
 * @param {import('react').RefObject<HTMLElement | null>} ref Elemento que se desliza.
 * @returns {{ isRendered: boolean }} Si el panel debe estar montado.
 */
export function useSlideAnimation(isOpen, ref) {
  const reducedMotion = useReducedMotion()
  const [closing, setClosing] = useState(false)
  const [wasOpen, setWasOpen] = useState(isOpen)

  // Estado derivado durante el render: al pasar de abierto a cerrado, el panel
  // se mantiene montado mientras dura la animación de salida.
  if (wasOpen !== isOpen) {
    setWasOpen(isOpen)
    setClosing(!isOpen && !reducedMotion)
  }

  useLayoutEffect(() => {
    const element = ref.current
    if (!element || reducedMotion) return undefined

    if (isOpen) {
      const animation = animate(element, { translateX: ['100%', '0%'], ...motionPresets.panelSlide })
      return () => animation.revert()
    }
    if (closing) {
      const animation = animate(element, {
        translateX: ['0%', '100%'],
        ...motionPresets.panelSlide,
        onComplete: () => setClosing(false),
      })
      return () => animation.pause()
    }
    return undefined
  }, [isOpen, closing, reducedMotion, ref])

  return { isRendered: isOpen || closing }
}
