/**
 * Contrato `SeasonInfo` con la spec 002 (plan §3.6).
 *
 * @typedef {object} SeasonInfo
 * @property {number} year Año de la temporada actual (spec 002, RF-2 y RF-3).
 */

/**
 * PROVISIONAL (decisión P-6 del plan, nota en RF-58 de la spec 001):
 * hasta que exista la spec 003 (obtención de datos), el año se mantiene a mano
 * y hay que actualizarlo en cada cambio de temporada.
 *
 * @type {SeasonInfo}
 */
export const currentSeason = Object.freeze({ year: 2026 })
