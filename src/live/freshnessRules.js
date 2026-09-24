/**
 * Reglas de frescura de los bloques con datos de la liga (spec 003: RF-89, RF-91, RF-92,
 * RF-155 a RF-159; plan §2.6). Funciones puras: el aspecto lo decide cada spec visual (plan D-12).
 */

/** Umbral de desactualización: 60 s el en vivo, 1 h el resto (glosario de la spec). */
export const STALE_THRESHOLD_MS = { live: 60_000, rest: 3_600_000 }

/**
 * Última actualización de un bloque: el cambio más reciente de lo que muestra (RF-157); si no
 * muestra nada, el último cambio del conjunto de datos que vigila (RF-158).
 *
 * @param {{ changedAt?: string | null }[]} items
 * @param {string | null} datasetLastChangedAt
 * @returns {string | null}
 */
export function lastUpdatedOf(items, datasetLastChangedAt) {
  const stamps = items.map((item) => item?.changedAt).filter(Boolean)
  if (stamps.length === 0) return datasetLastChangedAt ?? null
  return stamps.reduce((latest, stamp) => (Date.parse(stamp) > Date.parse(latest) ? stamp : latest))
}

/**
 * Datos sin actualizar: el servidor lo dice (fuente sin consultas con éxito), o el canal entre
 * la página y Retake lleva cortado más que el umbral del conjunto (RF-89). El aviso se retira
 * en cuanto vuelve a actualizarse (RF-92).
 *
 * @param {{ dataset: string, serverStale: boolean, cutSince: number | null, now: number }} params
 */
export function isStale({ dataset, serverStale, cutSince, now }) {
  if (serverStale) return true
  if (cutSince == null) return false
  const threshold = dataset === 'live' ? STALE_THRESHOLD_MS.live : STALE_THRESHOLD_MS.rest
  return now - cutSince > threshold
}

/**
 * Texto de la última actualización en el idioma activo (RF-155).
 *
 * @param {string | null} iso
 * @param {string} locale
 * @param {(key: string, values?: object) => string} t
 * @param {string} [timeZone] Por defecto, la del dispositivo.
 */
export function formatLastUpdated(iso, locale, t, timeZone) {
  if (!iso) return t('live.neverUpdated')
  const when = new Intl.DateTimeFormat(locale, { dateStyle: 'long', timeStyle: 'short', timeZone }).format(new Date(iso))
  return t('live.lastUpdated', { when })
}
