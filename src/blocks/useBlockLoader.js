import { useCallback, useEffect, useReducer, useRef } from 'react'
import { BLOCK_LOAD_TIMEOUT_MS } from '../config/layoutConstants.js'
import { useConnection } from '../connection/ConnectionProvider.jsx'
import { blockLoaderReducer, initialBlockLoadState } from './blockLoaderMachine.js'

/**
 * Cargador de un bloque con contenido (plan §1.6 y §3.4).
 *
 * - Cada intento tiene su propia ventana de 15 s; al agotarla se muestra el
 *   error, pero la petición NO se cancela (RF-42, D-5).
 * - Si los datos llegan después del error, sustituyen al aviso (RF-43).
 * - "Reintentar" no tiene límite, pero solo hay un intento en curso (RF-45, RF-46, D-6).
 * - Al volver la red, el bloque en error reintenta solo (RF-53).
 *
 * Cada bloque tiene su propio cargador, así que el fallo de uno no afecta a
 * los demás (RF-48). El estado vive en el componente, no en el diseño, así que
 * se conserva al redimensionar (RF-49, D-1).
 *
 * @template T
 * @param {() => Promise<T>} load Operación que obtiene los datos del bloque.
 * @param {{ timeoutMs?: number }} [options]
 * @returns {{ state: import('./blockLoaderMachine.js').BlockLoadState, retry: () => void }}
 */
export function useBlockLoader(load, { timeoutMs = BLOCK_LOAD_TIMEOUT_MS } = {}) {
  const [state, dispatch] = useReducer(blockLoaderReducer, initialBlockLoadState)
  const { onReconnect } = useConnection()

  // Refs para decidir de forma síncrona, aunque React aún no haya repintado.
  const attemptRef = useRef(0)
  const inFlightRef = useRef(false)
  const statusRef = useRef(state.status)
  const timerRef = useRef(null)
  // `false` tras desmontar: los resultados que lleguen después se ignoran.
  const mountedRef = useRef(false)
  const loadRef = useRef(load)
  loadRef.current = load
  statusRef.current = state.status

  const startAttempt = useCallback(() => {
    if (inFlightRef.current) return
    const attempt = attemptRef.current + 1
    attemptRef.current = attempt
    inFlightRef.current = true
    statusRef.current = 'loading'
    dispatch({ type: 'start', attempt })

    const isCurrentMount = () => mountedRef.current
    const endWindow = () => {
      if (attemptRef.current === attempt) {
        inFlightRef.current = false
        clearTimeout(timerRef.current)
      }
    }

    timerRef.current = setTimeout(() => {
      if (!isCurrentMount()) return
      endWindow()
      dispatch({ type: 'timeout', attempt })
    }, timeoutMs)

    let request
    try {
      request = Promise.resolve(loadRef.current())
    } catch (error) {
      request = Promise.reject(error)
    }
    request.then(
        (data) => {
          if (!isCurrentMount()) return
          endWindow()
          dispatch({ type: 'resolve', attempt, data })
        },
        () => {
          if (!isCurrentMount()) return
          endWindow()
          dispatch({ type: 'reject', attempt })
        },
      )
  }, [timeoutMs])

  // Primer intento al montar el bloque. Solo se lanza una vez por instancia:
  // el doble montaje de StrictMode en desarrollo no provoca una segunda carga.
  useEffect(() => {
    mountedRef.current = true
    if (attemptRef.current === 0) startAttempt()
    return () => {
      mountedRef.current = false
    }
  }, [startAttempt])

  // Reintento automático al recuperar la conexión (RF-53).
  useEffect(
    () =>
      onReconnect(() => {
        if (statusRef.current === 'error') startAttempt()
      }),
    [onReconnect, startAttempt],
  )

  return { state, retry: startAttempt }
}
