import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router'
import { WIDE_MEDIA_QUERY } from '../config/layoutConstants.js'

/**
 * Estado abierto/cerrado del panel de navegación móvil (plan §1.4).
 *
 * El panel se cierra:
 * - al cambiar de dirección, incluidos Atrás y Adelante del navegador (RF-28, RF-29);
 * - con la tecla Escape (RF-21);
 * - cuando la ventana pasa a medir 1024 px o más (RF-23).
 * El cierre al pulsar una entrada o fuera del panel lo hace el propio panel (RF-20, RF-21).
 *
 * @returns {{ isOpen: boolean, open: () => void, close: () => void, toggle: () => void }}
 */
export function useNavPanelState() {
  const [isOpen, setIsOpen] = useState(false)
  const location = useLocation()
  const lastKey = useRef(location.key)

  const open = useCallback(() => setIsOpen(true), [])
  const close = useCallback(() => setIsOpen(false), [])
  const toggle = useCallback(() => setIsOpen((value) => !value), [])

  // Cambio de dirección.
  useEffect(() => {
    if (lastKey.current !== location.key) {
      lastKey.current = location.key
      setIsOpen(false)
    }
  }, [location.key])

  // Tecla Escape.
  useEffect(() => {
    if (!isOpen) return undefined
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setIsOpen(false)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [isOpen])

  // Paso a pantalla ancha.
  useEffect(() => {
    const media = window.matchMedia?.(WIDE_MEDIA_QUERY)
    if (!media) return undefined
    const onChange = () => {
      if (media.matches) setIsOpen(false)
    }
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])

  return { isOpen, open, close, toggle }
}
