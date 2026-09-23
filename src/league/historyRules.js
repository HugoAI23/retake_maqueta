/**
 * Reglas de presentación del historial de campeonatos (spec 002, §2.9).
 */
import { ACRONYMS, orNotAvailable } from './labels.js'

/**
 * Lugar de un equipo tal como se publicó: `1`, `9-12` o `DQ` (RF-8, RF-9).
 * @param {{ place: string | null, isDq: boolean }} placement
 * @param {import('i18next').TFunction} t
 */
export function formatPlace(placement, t) {
  if (placement.isDq) return ACRONYMS.DQ
  return orNotAvailable(placement.place, t)
}

/**
 * Gamertags de un jugador en un roster histórico: el de esa final junto al actual,
 * o uno solo si coinciden (RF-69, RF-112).
 * @param {{ gamertagAtFinal: string | null, currentGamertag: string }} entry
 * @returns {string[]}
 */
export function formatRosterGamertag(entry) {
  const { gamertagAtFinal, currentGamertag } = entry
  return gamertagAtFinal && gamertagAtFinal !== currentGamertag ? [gamertagAtFinal, currentGamertag] : [currentGamertag]
}

/**
 * Dato de un campeonato del historial, o `No disponible` si falta (RF-120).
 * @param {unknown} value
 * @param {import('i18next').TFunction} t
 */
export function formatHistoryField(value, t) {
  return orNotAvailable(value, t)
}
