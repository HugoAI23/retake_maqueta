import { useEffect } from 'react'

/** Contenedor de la aplicación que se vuelve inerte mientras el panel está abierto. */
const APP_ROOT_ID = 'root'

/**
 * Mantiene el foco dentro del panel mientras está abierto (RF-82, plan D-10).
 *
 * El panel se pinta fuera de #root (en un portal), así que basta con marcar
 * #root como `inert`: el resto de la página deja de recibir foco y queda
 * oculto a los lectores de pantalla. Al cerrar, el foco vuelve al botón de
 * menú (RF-83).
 *
 * @param {boolean} isOpen
 * @param {import('react').RefObject<HTMLElement | null>} containerRef Panel.
 * @param {import('react').RefObject<HTMLElement | null>} returnFocusRef Botón de menú.
 */
export function useFocusContainment(isOpen, containerRef, returnFocusRef) {
  useEffect(() => {
    if (!isOpen) return undefined
    const root = document.getElementById(APP_ROOT_ID)
    root?.setAttribute('inert', '')
    containerRef.current?.querySelector('button, a[href]')?.focus()

    return () => {
      root?.removeAttribute('inert')
      returnFocusRef.current?.focus()
    }
  }, [isOpen, containerRef, returnFocusRef])
}
