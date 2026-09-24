/**
 * Canal de eventos del servidor de una pestaña (spec 003: RF-79, RF-82, RF-89; plan §2.6 y §3.3).
 *
 * - Una sola conexión a `/api/stream` por pestaña, compartida por todos los bloques.
 * - Se cierra al ocultar la pestaña (no gasta nada en segundo plano) y se reabre al volver;
 *   entonces avisa con `{ type: 'visible' }` para que los bloques se pongan al día (RF-82).
 * - Si pasan 45 s sin ningún mensaje (el servidor envía un latido cada 15 s), da el canal por
 *   cortado (`cutSince`); el navegador sigue reintentando solo (`retry: 5000`).
 * - Los datos no viajan por aquí: cada bloque los vuelve a pedir a su ruta.
 */

export const HEARTBEAT_TIMEOUT_MS = 45_000
const EVENT_TYPES = ['change', 'freshness', 'heartbeat']

/**
 * @typedef {{ type: 'change', datasets: string[], changedAt: string }
 *   | { type: 'freshness', stale: Record<string, boolean> }
 *   | { type: 'heartbeat' }
 *   | { type: 'visible' }
 *   | { type: 'status', cutSince: number | null }} LiveEvent
 */

/**
 * @param {{
 *   url?: string,
 *   EventSourceImpl?: typeof EventSource,
 *   doc?: Document,
 *   now?: () => number,
 * }} [options] Todo inyectable para las pruebas.
 */
export function createLiveChannel({
  url = '/api/stream',
  EventSourceImpl = globalThis.EventSource,
  doc = globalThis.document,
  now = () => Date.now(),
} = {}) {
  const listeners = new Set()
  let source = null
  let watchdog = null
  let cutSince = null
  let started = false

  const emit = (event) => listeners.forEach((fn) => fn(event))

  const setCut = (value) => {
    if (value === cutSince) return
    cutSince = value
    emit({ type: 'status', cutSince })
  }

  const armWatchdog = () => {
    clearTimeout(watchdog)
    watchdog = setTimeout(() => setCut(now()), HEARTBEAT_TIMEOUT_MS)
  }

  const alive = () => {
    setCut(null)
    armWatchdog()
  }

  const open = () => {
    if (!EventSourceImpl || source || doc?.visibilityState === 'hidden') return
    source = new EventSourceImpl(url)
    source.addEventListener('open', alive)
    for (const type of EVENT_TYPES) {
      source.addEventListener(type, (message) => {
        alive()
        let data = {}
        try {
          data = JSON.parse(message.data)
        } catch {
          return
        }
        if (type === 'change') emit({ type, datasets: data.datasets ?? [], changedAt: data.changedAt ?? null })
        else if (type === 'freshness') emit({ type, stale: data })
        else emit({ type })
      })
    }
    armWatchdog()
  }

  const shut = () => {
    clearTimeout(watchdog)
    watchdog = null
    source?.close()
    source = null
  }

  const onVisibility = () => {
    if (doc.visibilityState === 'hidden') {
      shut()
      setCut(null) // en segundo plano no se actualiza nada, pero no es un corte (RF-82)
    } else {
      open()
      emit({ type: 'visible' })
    }
  }

  return {
    /** @param {(event: LiveEvent) => void} listener @returns {() => void} */
    subscribe(listener) {
      listeners.add(listener)
      if (!started) {
        started = true
        doc?.addEventListener?.('visibilitychange', onVisibility)
        open()
      }
      return () => listeners.delete(listener)
    },
    getStatus: () => ({ cutSince }),
    close() {
      shut()
      doc?.removeEventListener?.('visibilitychange', onVisibility)
      listeners.clear()
      started = false
    },
  }
}
