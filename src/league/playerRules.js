/**
 * Reglas de presentación de los jugadores (spec 002, §2.9).
 */
import { ACRONYMS, leagueText, orNotAvailable } from './labels.js'

/**
 * Edad en años cumplidos (en UTC, calculada en el servidor): exacta o como rango de
 * dos edades (RF-23, RF-108). La fecha de nacimiento nunca llega al navegador (RF-24).
 * @param {{ min: number, max: number } | null} age
 * @param {import('i18next').TFunction} t
 */
export function formatAge(age, t) {
  if (!age) return leagueText(t, 'notAvailable')
  return age.min === age.max ? String(age.min) : `${age.min}–${age.max}`
}

/**
 * Nombre real o país, o `No disponible` si no está registrado (RF-25).
 * @param {string | null} value
 * @param {import('i18next').TFunction} t
 */
export function formatPersonalField(value, t) {
  return orNotAvailable(value, t)
}

/**
 * Rol del jugador (`SMG` o `AR`, sin traducir) o `Sin rol` (RF-71, RF-125).
 * @param {'SMG' | 'AR' | null} role
 * @param {import('i18next').TFunction} t
 */
export function formatRole(role, t) {
  return role && ACRONYMS[role] ? ACRONYMS[role] : leagueText(t, 'noRole')
}

/**
 * Equipo del jugador o `Agente libre` (RF-107).
 * @param {{ isFreeAgent: boolean }} player
 * @param {string | null} teamName Nombre de la identidad de su equipo, si tiene.
 * @param {import('i18next').TFunction} t
 */
export function formatTeam(player, teamName, t) {
  if (player.isFreeAgent) return leagueText(t, 'freeAgent')
  return orNotAvailable(teamName, t)
}

/**
 * Fuera del historial de campeonatos, el jugador se muestra con su gamertag actual (RF-68).
 * @param {{ currentGamertag: string }} player
 */
export function currentGamertag(player) {
  return player.currentGamertag
}
