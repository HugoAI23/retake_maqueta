/**
 * Reglas de presentación de partidos, mapas y estadísticas (spec 002, §2.9).
 */
import { leagueText, orNotAvailable } from './labels.js'

/** Estadísticas de jugador por mapa (RF-41 a RF-44), con los nombres de la API. */
export const STAT_KEYS = Object.freeze([
  'kills', 'deaths', 'kd', 'damage', 'assists', 'hillTime', 'contestedHillTime',
  'firstBloods', 'firstDeaths', 'plants', 'defuses', 'zoneCaptures', 'overloads',
])

const PHASE_KEYS = Object.freeze({
  week: 'week',
  group: 'group',
  winners_bracket: 'winnersBracket',
  losers_bracket: 'losersBracket',
  grand_final: 'grandFinal',
})

/**
 * Fecha y hora de un partido en la zona horaria del dispositivo (RF-70), con el mismo
 * formato que `formatDateTime` de la spec 001.
 * @param {string | null} iso Fecha y hora ISO 8601 en UTC.
 * @param {'es' | 'en'} locale
 * @param {{ timeZone?: string }} [options] Zona horaria concreta (solo para pruebas).
 */
export function formatMatchDateTime(iso, locale, { timeZone } = {}) {
  if (!iso) return null
  return new Intl.DateTimeFormat(locale, { dateStyle: 'long', timeStyle: 'short', timeZone }).format(new Date(iso))
}

/**
 * Nombre de un lado del partido (RF-85, RF-86):
 * el equipo, "Ganador de…" / "Perdedor de…" o `Por definir`.
 * @param {{ identity: { shortName: string } | null, origin: { matchId: string, outcome: 'winner' | 'loser' } | null }} slot
 * @param {import('i18next').TFunction} t
 * @param {(matchId: string) => string} describeMatch Cómo nombrar el partido de origen (lo decide cada spec visual).
 */
export function formatSlot(slot, t, describeMatch) {
  if (slot.identity) return slot.identity.shortName
  if (slot.origin) {
    const key = slot.origin.outcome === 'winner' ? 'winnerOf' : 'loserOf'
    return leagueText(t, key, { match: describeMatch(slot.origin.matchId) })
  }
  return leagueText(t, 'toBeDecided')
}

function scoreText(score) {
  return score && score[0] !== null && score[1] !== null ? `${score[0]}–${score[1]}` : null
}

/**
 * Marcador del mapa en curso de un partido en vivo, o `No disponible` (RF-90).
 * @param {{ score: Array<number | null> | null } | null} liveMap
 * @param {import('i18next').TFunction} t
 */
export function formatLiveMapScore(liveMap, t) {
  return scoreText(liveMap?.score) ?? leagueText(t, 'notAvailable')
}

/**
 * Mapas de un partido en orden: los no jugados llevan `No jugado` y no tienen marcador (RF-94).
 * @param {Array<{ position: number, played: boolean, score: Array<number | null> | null }>} maps
 * @param {import('i18next').TFunction} t
 */
export function displayMaps(maps, t) {
  return [...maps]
    .sort((a, b) => a.position - b.position)
    .map((map) => ({
      ...map,
      scoreText: map.played ? scoreText(map.score) : null,
      notPlayedLabel: map.played ? null : leagueText(t, 'notPlayed'),
    }))
}

/**
 * Una estadística: el número (también 0) o `No disponible` si no se publicó (RF-46).
 * @param {number | null} value
 * @param {import('i18next').TFunction} t
 */
export function formatStat(value, t) {
  return orNotAvailable(value, t)
}

/**
 * ¿Hay que mostrar "Estadísticas pendientes" junto al marcador final? (RF-47, RF-48, RF-72)
 *
 * Sí, si el partido está finalizado y algún mapa jugado no tiene estadísticas de nadie o
 * tiene algún jugador sin ninguna estadística. Una estadística suelta que falte no cuenta.
 * El aviso desaparece solo cuando llegan los datos.
 * @param {{ status: string, maps: Array<{ played: boolean, stats: object[] }> }} match
 */
export function needsStatsPendingNotice(match) {
  if (match.status !== 'finished') return false
  return match.maps.some(
    (map) =>
      map.played &&
      (map.stats.length === 0 || map.stats.some((row) => STAT_KEYS.every((key) => row[key] === null || row[key] === undefined))),
  )
}

/**
 * Fase traducida, o `No disponible` si el partido no tiene fase (RF-126, RF-135).
 * @param {string | null} phase Fase de la API (`grand_final`, `winners_bracket`…).
 * @param {import('i18next').TFunction} t
 */
export function formatPhase(phase, t) {
  const key = phase ? PHASE_KEYS[phase] : null
  return key ? leagueText(t, `phase.${key}`) : leagueText(t, 'notAvailable')
}
