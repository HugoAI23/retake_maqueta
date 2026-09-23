/**
 * Disponibilidad de la tabla de posiciones (spec 002, RF-51 y decisión A-22).
 */
import { leagueText } from './labels.js'

/**
 * La tabla no está disponible si no hay filas o ningún equipo tiene puntos
 * (todos sin puntos o a 0, como al empezar la temporada).
 * @param {Array<{ points: number | null }>} rows
 */
export function isStandingsAvailable(rows) {
  return rows.some((row) => typeof row.points === 'number' && row.points > 0)
}

/** @param {import('i18next').TFunction} t */
export function standingsUnavailableText(t) {
  return leagueText(t, 'standingsUnavailable')
}
