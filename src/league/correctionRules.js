/**
 * Datos corregidos (spec 002, RF-99): junto a un dato marcado se muestra `Corregido`
 * (`leagueText(t, 'corrected')`).
 */

/**
 * ¿Está marcado como corregido este campo de la fila?
 * @param {{ correctedFields: string[] }} row Fila de la API (partido, mapa, estadísticas o clasificación).
 * @param {string} field Nombre del campo tal como lo devuelve `correctedFields` (p. ej. `score_2`).
 */
export function isCorrected(row, field) {
  return row.correctedFields.includes(field)
}
