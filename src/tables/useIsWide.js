import { useSyncExternalStore } from 'react'
import { WIDE_MEDIA_QUERY } from '../config/layoutConstants.js'

function subscribe(onChange) {
  const media = window.matchMedia?.(WIDE_MEDIA_QUERY)
  if (!media) return () => {}
  media.addEventListener('change', onChange)
  return () => media.removeEventListener('change', onChange)
}

function getSnapshot() {
  return Boolean(window.matchMedia?.(WIDE_MEDIA_QUERY)?.matches)
}

/**
 * Si la ventana mide 1024 px de ancho o más (spec 004, RF-14, RF-15). Cambia al cruzar
 * ese ancho, sin recargar. Lo usan la celda de equipo y el orden por defecto de las
 * secciones, que depende del texto que se ve (RF-47).
 */
export function useIsWide() {
  return useSyncExternalStore(subscribe, getSnapshot, () => false)
}
