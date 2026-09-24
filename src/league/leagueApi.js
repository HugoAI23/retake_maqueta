/**
 * Cliente de la API de solo lectura de la liga (spec 002, plan §1.4, §2.3 y D-11).
 *
 * Cada función devuelve los datos o falla con un `LeagueApiError`, así se puede pasar
 * directamente como `load` al cargador de bloques de la spec 001 (esqueleto, error y
 * "Reintentar" incluidos). En desarrollo, Vite redirige `/api` al backend.
 */

const BASE_URL = '/api'

/**
 * @typedef {object} Identity
 * @property {string} id
 * @property {string} shortName
 * @property {string | null} abbreviation
 * @property {string | null} logoUrl
 * @property {string | null} primaryColor
 * @property {string | null} secondaryColor
 * @property {string} validFrom Fecha y hora ISO 8601 en UTC.
 *
 * @typedef {{ id: string, identities: Identity[] }} Franchise
 * @typedef {{ year: number, name: string | null, startedAt: string }} Season
 * @typedef {{ id: string, name: string, seasonYear: number }} LeagueEvent
 * @typedef {{ min: number, max: number }} AgeRange Edad en UTC: `min === max` si es exacta.
 *
 * @typedef {object} Player
 * @property {string} id
 * @property {string} currentGamertag
 * @property {string[]} previousGamertags
 * @property {string | null} realName
 * @property {string | null} country
 * @property {AgeRange | null} age
 * @property {'SMG' | 'AR' | null} role Nulo = sin rol.
 * @property {string | null} teamFranchiseId
 * @property {boolean} isCurrentSeason
 * @property {boolean} isFreeAgent
 * @property {string[]} championshipIds
 *
 * @typedef {{ matchId: string, outcome: 'winner' | 'loser' }} Origin
 * @typedef {{ franchiseId: string | null, identity: Identity | null, origin: Origin | null }} Slot
 *
 * @typedef {object} PlayerStats Estadísticas de un jugador en un mapa; nulo = no publicada.
 * @property {string} playerId
 * @property {string | null} franchiseId
 * @property {boolean} isSubstitute
 * @property {number | null} kills
 * @property {number | null} deaths
 * @property {number | null} kd
 * @property {number | null} damage
 * @property {number | null} assists
 * @property {number | null} hillTime
 * @property {number | null} contestedHillTime
 * @property {number | null} firstBloods
 * @property {number | null} firstDeaths
 * @property {number | null} plants
 * @property {number | null} defuses
 * @property {number | null} zoneCaptures
 * @property {number | null} overloads
 * @property {string[]} correctedFields
 *
 * @typedef {object} MatchMap
 * @property {number} position
 * @property {string | null} mode
 * @property {string | null} mapName
 * @property {boolean} played
 * @property {Array<number | null> | null} score
 * @property {number | null} winnerSide
 * @property {string[]} correctedFields
 * @property {PlayerStats[]} stats
 *
 * @typedef {object} Match
 * @property {string} id
 * @property {string} eventId
 * @property {string} eventName
 * @property {string | null} phase
 * @property {number} bestOf
 * @property {'scheduled' | 'live' | 'finished'} status
 * @property {string | null} scheduledAt
 * @property {string[]} scheduleHistory
 * @property {Slot[]} slots
 * @property {Array<number | null> | null} mapsWon
 * @property {{ mode: string | null, score: Array<number | null> | null } | null} liveMap
 * @property {number | null} winnerSide
 * @property {string[]} correctedFields
 * @property {MatchMap[]} maps
 *
 * @typedef {{ franchiseId: string, identity: Identity | null, position: number | null, points: number | null }} StandingRow
 *
 * @typedef {object} Placement
 * @property {string} franchiseId
 * @property {Identity | null} identity
 * @property {string | null} place
 * @property {boolean} isDq
 * @property {number | null} prizeUsd
 * @property {number | null} poolPercent
 * @property {Array<{ playerId: string, gamertagAtFinal: string | null, currentGamertag: string }>} roster
 * @property {string[]} correctedFields
 *
 * @typedef {object} Championship
 * @property {string} id
 * @property {number} year
 * @property {string | null} competition
 * @property {string | null} gameName
 * @property {string | null} gameAbbreviation
 * @property {string | null} finalDate
 * @property {Placement[]} placements
 */

/** Error de la API: `status` es el código HTTP, o 0 si no hubo respuesta (sin red). */
export class LeagueApiError extends Error {
  /**
   * @param {string} message
   * @param {number} status
   */
  constructor(message, status) {
    super(message)
    this.name = 'LeagueApiError'
    this.status = status
  }
}

async function request(path, { allowNotFound = false } = {}) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, { headers: { Accept: 'application/json' } })
  } catch (error) {
    throw new LeagueApiError(`No se pudo contactar con la API (${path}): ${error.message}`, 0)
  }
  if (allowNotFound && response.status === 404) return null
  if (!response.ok) throw new LeagueApiError(`La API respondió ${response.status} en ${path}`, response.status)
  return response.json()
}

/** @returns {Promise<Season | null>} Temporada actual, o `null` si ninguna ha empezado. */
export const getCurrentSeason = () => request('/season/current', { allowNotFound: true })
/** @returns {Promise<Franchise[]>} */
export const getFranchises = () => request('/franchises')
/** @returns {Promise<Player[]>} */
export const getPlayers = () => request('/players')
/** @param {string} id @returns {Promise<Player>} */
export const getPlayer = (id) => request(`/players/${encodeURIComponent(id)}`)
/** @returns {Promise<LeagueEvent[]>} */
export const getEvents = () => request('/events')
/** @returns {Promise<Match[]>} */
export const getMatches = () => request('/matches')
/** @param {string} id @returns {Promise<Match>} */
export const getMatch = (id) => request(`/matches/${encodeURIComponent(id)}`)
/** @returns {Promise<StandingRow[]>} */
export const getStandings = () => request('/standings')
/** @returns {Promise<Championship[]>} */
export const getChampionships = () => request('/championships')
/**
 * Frescura de cada conjunto de datos (spec 003: RF-89, RF-155, RF-158).
 * @returns {Promise<Record<string, { lastChangedAt: string | null, stale: boolean }>>}
 */
export const getFreshness = () => request('/freshness')
