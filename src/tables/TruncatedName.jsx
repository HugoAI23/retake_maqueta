import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

/** Tiempo para pasar el puntero del nombre a la burbuja sin que se cierre (RF-17b). */
const HOVER_GRACE_MS = 150
/** Margen mínimo entre la burbuja y el borde de la ventana (riesgo R-2). */
const EDGE_MARGIN = 8
/** Separación entre el nombre y la burbuja. */
const GAP = 4

/**
 * Nombre que se recorta con puntos suspensivos si no cabe (spec 004, RF-17, RF-17a, RF-17b;
 * plan §2.6, decisión H-2: componente propio).
 *
 * Solo si no cabe:
 * - recibe el foco del teclado aunque no sea un enlace (RF-17a);
 * - muestra el nombre completo en una burbuja (`role="tooltip"`, asociada con `aria-describedby`)
 *   al pasar el puntero, con el foco o con un toque (RF-17);
 * - la burbuja se cierra con Escape sin mover el foco ni el puntero, se puede recorrer con el
 *   puntero y sigue abierta mientras el puntero o el foco estén en el nombre (WCAG 1.4.13).
 *
 * La burbuja se pinta en `document.body` con posición fija: así no la recorta la caja con
 * desplazamiento de la tabla ni la tapan las columnas fijas, y se ajusta al borde de la ventana.
 *
 * @param {{ text: string, className?: string }} props
 */
export function TruncatedName({ text, className = '' }) {
  const tooltipId = useId()
  const nameRef = useRef(null)
  const tooltipRef = useRef(null)
  const leaveTimer = useRef(null)
  const [truncated, setTruncated] = useState(false)
  const [hoverName, setHoverName] = useState(false)
  const [hoverTip, setHoverTip] = useState(false)
  const [focused, setFocused] = useState(false)
  const [tapped, setTapped] = useState(false)
  const [dismissed, setDismissed] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  const open = truncated && !dismissed && (hoverName || hoverTip || focused || tapped)

  // ¿Cabe el nombre? Se vuelve a medir si cambia el tamaño de su caja o el texto.
  useLayoutEffect(() => {
    const node = nameRef.current
    if (!node) return undefined
    const measure = () => setTruncated(node.scrollWidth > node.clientWidth)
    measure()
    if (typeof ResizeObserver === 'undefined') return undefined
    const observer = new ResizeObserver(measure)
    observer.observe(node)
    return () => observer.disconnect()
  }, [text])

  const place = useCallback(() => {
    const name = nameRef.current?.getBoundingClientRect()
    const tip = tooltipRef.current?.getBoundingClientRect()
    if (!name || !tip) return
    const maxLeft = window.innerWidth - tip.width - EDGE_MARGIN
    setPosition({
      top: name.bottom + GAP,
      left: Math.max(EDGE_MARGIN, Math.min(name.left, maxLeft)),
    })
  }, [])

  // Colocación debajo del nombre, también al desplazar o cambiar el tamaño de la ventana.
  useLayoutEffect(() => {
    if (!open) return undefined
    place()
    window.addEventListener('scroll', place, true)
    window.addEventListener('resize', place)
    return () => {
      window.removeEventListener('scroll', place, true)
      window.removeEventListener('resize', place)
    }
  }, [open, place])

  // Escape la cierra; un toque fuera del nombre y de la burbuja, también.
  useEffect(() => {
    if (!open) return undefined
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setDismissed(true)
    }
    const onPointerDown = (event) => {
      if (nameRef.current?.contains(event.target) || tooltipRef.current?.contains(event.target)) return
      setTapped(false)
    }
    document.addEventListener('keydown', onKeyDown)
    document.addEventListener('pointerdown', onPointerDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.removeEventListener('pointerdown', onPointerDown)
    }
  }, [open])

  useEffect(() => () => clearTimeout(leaveTimer.current), [])

  const enterName = () => {
    clearTimeout(leaveTimer.current)
    setDismissed(false)
    setHoverName(true)
  }
  const leaveName = () => {
    clearTimeout(leaveTimer.current)
    leaveTimer.current = setTimeout(() => setHoverName(false), HOVER_GRACE_MS)
  }
  const enterTip = () => {
    clearTimeout(leaveTimer.current)
    setHoverTip(true)
  }
  const leaveTip = () => {
    setHoverTip(false)
    leaveName()
  }

  return (
    <>
      <span
        ref={nameRef}
        data-truncated-name
        className={`block truncate ${className}`}
        tabIndex={truncated ? 0 : undefined}
        aria-describedby={open ? tooltipId : undefined}
        onPointerEnter={truncated ? enterName : undefined}
        onPointerLeave={truncated ? leaveName : undefined}
        onFocus={
          truncated
            ? () => {
                setDismissed(false)
                setFocused(true)
              }
            : undefined
        }
        onBlur={
          truncated
            ? () => {
                setFocused(false)
                setTapped(false)
              }
            : undefined
        }
        onClick={
          truncated
            ? () => {
                setDismissed(false)
                setTapped(true)
              }
            : undefined
        }
      >
        {text}
      </span>
      {open &&
        createPortal(
          <span
            ref={tooltipRef}
            id={tooltipId}
            role="tooltip"
            onPointerEnter={enterTip}
            onPointerLeave={leaveTip}
            style={{ top: position.top, left: position.left }}
            className="fixed z-50 max-w-[calc(100vw-16px)] rounded-md border border-border bg-raised px-2 py-1 text-sm text-text shadow-lg"
          >
            {text}
          </span>,
          document.body,
        )}
    </>
  )
}
