/**
 * Orden de las filas de una tabla de datos (spec 004, RF-2, RF-7 a RF-9).
 *
 * La página entrega las filas ya en su orden por defecto (RF-2). Al ordenar por una
 * columna, los empates conservan ese orden (RF-7) y las filas sin valor van detrás
 * en los dos sentidos (RF-9).
 */

/**
 * Tipo de orden de una columna: qué significa «de mejor a peor» (RF-8, RF-49).
 * - `ascending`: menor es mejor (p. ej. Posición).
 * - `descending`: mayor es mejor (p. ej. Puntos).
 * - `text`: alfabético con las reglas del idioma (RF-7a).
 * - `record`: balance ganados–perdidos, por porcentaje de victorias y más ganadas (RF-8).
 * - `null`: columna excluida del orden.
 * @typedef {'ascending' | 'descending' | 'text' | 'record' | null} SortKind
 */

/**
 * Valor comparable de una celda, o `null` si la fila no tiene valor (RF-9).
 * Un balance sin partidos jugados (`0–0`) tampoco tiene valor.
 *
 * @param {SortKind} kind
 * @param {unknown} value
 */
function comparable(kind, value) {
  if (value === null || value === undefined) return null
  if (kind === 'record') {
    const played = value.won + value.lost
    return played > 0 ? value : null
  }
  if (kind === 'text') return String(value)
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

/**
 * Comparador «de mejor a peor» de dos valores con valor.
 * @returns {number} negativo si `a` es mejor que `b`.
 */
function bestFirst(kind, a, b, collator) {
  switch (kind) {
    case 'ascending':
      return a - b
    case 'descending':
      return b - a
    case 'text':
      return collator.compare(a, b)
    case 'record': {
      // Porcentaje de victorias sin divisiones: a.won/(a.won+a.lost) frente a b.
      const byRate = b.won * (a.won + a.lost) - a.won * (b.won + b.lost)
      return byRate !== 0 ? byRate : b.won - a.won
    }
    default:
      return 0
  }
}

/**
 * Ordena las filas según el estado del orden.
 *
 * @template T
 * @param {T[]} rows Filas en el orden por defecto de la sección.
 * @param {Array<{ id: string, sortKind: SortKind, value: (row: T) => unknown }>} columns
 * @param {import('./sortCycle.js').SortState} state
 * @param {string} locale Idioma de la interfaz, para el orden alfabético (RF-7a).
 * @returns {T[]} Una lista nueva; la original no cambia.
 */
export function sortRows(rows, columns, state, locale) {
  const column = state && columns.find((c) => c.id === state.columnId)
  if (!column || !column.sortKind) return [...rows]

  const kind = column.sortKind
  const sign = state.direction === 'worst' ? -1 : 1
  const collator = new Intl.Collator(locale, { sensitivity: 'base', numeric: true })
  const keyed = rows.map((row, index) => ({ row, index, value: comparable(kind, column.value(row)) }))

  keyed.sort((a, b) => {
    if (a.value === null || b.value === null) {
      if (a.value === null && b.value === null) return a.index - b.index
      return a.value === null ? 1 : -1
    }
    return sign * bestFirst(kind, a.value, b.value, collator) || a.index - b.index
  })
  return keyed.map((k) => k.row)
}
