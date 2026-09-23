/**
 * Máquina de estados del cargador de bloques (plan §3.4, decisión D-4).
 *
 * Es una función pura (reducer): recibe el estado y un evento y devuelve el
 * estado siguiente. El hook useBlockLoader la conecta con los temporizadores,
 * la operación de carga y la conexión.
 *
 * @typedef {object} BlockLoadState
 * @property {'loading' | 'error' | 'ready'} status Estado visible del bloque.
 * @property {'failed' | 'timeout' | null} errorReason Motivo del error (el aviso visible es el mismo).
 * @property {unknown} data Datos del bloque; solo en `ready`.
 * @property {number} attempt Número del intento vigente.
 * @property {boolean} inFlight Si el intento vigente está dentro de su ventana de 15 s.
 *
 * @typedef {{ type: 'start', attempt: number }
 *   | { type: 'resolve', attempt: number, data: unknown }
 *   | { type: 'reject', attempt: number }
 *   | { type: 'timeout', attempt: number }} BlockLoadEvent
 */

/** @type {BlockLoadState} */
export const initialBlockLoadState = Object.freeze({
  status: 'loading',
  errorReason: null,
  data: undefined,
  attempt: 0,
  inFlight: false,
})

/**
 * @param {BlockLoadState} state
 * @param {BlockLoadEvent} event
 * @returns {BlockLoadState}
 */
export function blockLoaderReducer(state, event) {
  switch (event.type) {
    // Nuevo intento: al montar, al pulsar "Reintentar" o al volver la red (RF-40, RF-44, RF-53).
    case 'start':
      return { status: 'loading', errorReason: null, data: undefined, attempt: event.attempt, inFlight: true }

    // Llegan datos. Se aceptan de CUALQUIER intento, también de uno ya vencido,
    // porque RF-43 pide aprovechar los datos tardíos (D-6). Una vez en `ready`,
    // los resultados de intentos anteriores se descartan.
    case 'resolve':
      if (state.status === 'ready') return state
      return { status: 'ready', errorReason: null, data: event.data, attempt: state.attempt, inFlight: false }

    // La operación falla (RF-41). Solo cuenta el intento vigente y solo si sigue cargando.
    case 'reject':
      if (event.attempt !== state.attempt || state.status !== 'loading') return state
      return { ...state, status: 'error', errorReason: 'failed', inFlight: false }

    // Pasan 15 s sin respuesta (RF-42). La petición no se cancela (D-5).
    case 'timeout':
      if (event.attempt !== state.attempt || state.status !== 'loading') return state
      return { ...state, status: 'error', errorReason: 'timeout', inFlight: false }

    default:
      return state
  }
}
