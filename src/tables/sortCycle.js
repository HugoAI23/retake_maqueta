/**
 * Ciclo de orden de una columna de una tabla de datos (spec 004, RF-3 a RF-5).
 *
 * El estado del orden es `null` (orden por defecto de la sección) o la columna
 * elegida con su sentido. Los datos nuevos no lo cambian: solo lo cambia el
 * usuario al pulsar una cabecera (RF-5).
 */

/**
 * @typedef {'best' | 'worst'} SortDirection  De mejor a peor o de peor a mejor.
 * @typedef {{ columnId: string, direction: SortDirection } | null} SortState
 */

/**
 * Estado siguiente al pulsar la cabecera de una columna ordenable.
 *
 * - Misma columna: de mejor a peor → de peor a mejor → orden por defecto (RF-3).
 * - Otra columna: empieza de mejor a peor (RF-4).
 *
 * @param {SortState} state Estado actual.
 * @param {string} columnId Columna pulsada.
 * @returns {SortState}
 */
export function nextSortState(state, columnId) {
  if (state === null || state.columnId !== columnId) return { columnId, direction: 'best' }
  if (state.direction === 'best') return { columnId, direction: 'worst' }
  return null
}
