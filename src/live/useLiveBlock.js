import { useCallback, useEffect, useRef, useState } from 'react'
import { useBlockLoader } from '../blocks/useBlockLoader.js'
import { useLive } from './LiveProvider.jsx'

/** Ciclo de la página: 30 s en vivo y 5 min el resto (glosario de la spec 003). */
export const PAGE_CYCLE_MS = { live: 30_000, rest: 300_000 }
/** Tras volver a la pestaña, se pone al día en 5 s como máximo (RF-82). */
export const VISIBLE_RELOAD_MS = 0

/**
 * Cargador de un bloque que se actualiza solo (spec 003: RF-79 a RF-88; plan §2.6).
 *
 * - La primera carga es la de la 001: esqueleto, error y "Reintentar" (RF-40 a RF-53 de la 001).
 * - Después recarga en silencio cuando el canal avisa de un cambio de lo que muestra, al menos
 *   una vez por ciclo de la página y al volver a verse la pestaña. Nunca vuelve el esqueleto
 *   (RF-85); si una recarga falla, conserva los datos sin aviso de error ni "Reintentar" y lo
 *   intenta en el siguiente ciclo (RF-86, RF-87).
 * - El bloque no se vuelve a montar, así que la página conserva su estado y la vista no salta
 *   (RF-83, RF-84).
 *
 * @template T
 * @param {() => Promise<T>} load
 * @param {{ datasets: string[], cycle?: 'live' | 'rest' }} options
 */
export function useLiveBlock(load, { datasets, cycle = 'rest' }) {
  const { state, retry } = useBlockLoader(load)
  const { subscribe } = useLive()
  const [latest, setLatest] = useState(null)
  const loadRef = useRef(load)
  const readyRef = useRef(false)
  const inFlightRef = useRef(false)
  const mountedRef = useRef(true)
  loadRef.current = load
  readyRef.current = state.status === 'ready'

  const refresh = useCallback(() => {
    if (!readyRef.current || inFlightRef.current) return
    inFlightRef.current = true
    Promise.resolve()
      .then(() => loadRef.current())
      .then((data) => mountedRef.current && setLatest({ data }))
      .catch(() => {}) // se conservan los datos; se reintenta en el siguiente ciclo (RF-86)
      .finally(() => {
        inFlightRef.current = false
      })
  }, [])

  const datasetsKey = datasets.join(',')
  useEffect(() => {
    const watched = new Set(datasetsKey.split(','))
    let timer = null
    const unsubscribe = subscribe((event) => {
      if (event.type === 'change' && event.datasets.some((d) => watched.has(d))) refresh()
      if (event.type === 'visible') timer = setTimeout(refresh, VISIBLE_RELOAD_MS)
    })
    return () => {
      clearTimeout(timer)
      unsubscribe()
    }
  }, [subscribe, datasetsKey, refresh])

  useEffect(() => {
    const interval = setInterval(() => {
      if (globalThis.document?.visibilityState !== 'hidden') refresh()
    }, PAGE_CYCLE_MS[cycle])
    return () => clearInterval(interval)
  }, [cycle, refresh])

  useEffect(() => () => {
    mountedRef.current = false
  }, [])

  const shown = state.status === 'ready' && latest ? { ...state, data: latest.data } : state
  return { state: shown, retry, refresh }
}
