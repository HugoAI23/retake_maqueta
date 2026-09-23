import { describe, expect, it } from 'vitest'
import { colors } from '../config/designTokens.js'
import { createI18n } from '../i18n/createI18n.js'
import { contrastRatio } from '../shared/contrast.js'
import { isCorrected } from './correctionRules.js'
import { formatHistoryField, formatPlace, formatRosterGamertag } from './historyRules.js'
import { ACRONYMS, leagueText } from './labels.js'
import {
  displayMaps,
  formatLiveMapScore,
  formatMatchDateTime,
  formatPhase,
  formatSlot,
  formatStat,
  needsStatsPendingNotice,
} from './matchRules.js'
import { currentGamertag, formatAge, formatPersonalField, formatRole, formatTeam } from './playerRules.js'
import { isStandingsAvailable, standingsUnavailableText } from './standingsRules.js'
import { bestTextColor, resolveTeamBadge } from './teamBadge.js'

const es = createI18n('es').t
const en = createI18n('en').t

describe('etiquetas (T-062 · RF-125, RF-126)', () => {
  it('las siglas son iguales en español e inglés', () => {
    expect(ACRONYMS).toEqual({ DQ: 'DQ', SMG: 'SMG', AR: 'AR' })
    expect(formatRole('SMG', es)).toBe(formatRole('SMG', en))
    expect(formatPlace({ place: 'DQ', isDq: true }, en)).toBe('DQ')
  })

  it('el resto de etiquetas se traduce', () => {
    expect(leagueText(es, 'notAvailable')).toBe('No disponible')
    expect(leagueText(en, 'notAvailable')).toBe('Not available')
    expect(leagueText(en, 'freeAgent')).toBe('Free agent')
  })
})

describe('historial (T-063 · RF-8, RF-9, RF-69, RF-112, RF-120)', () => {
  it('lugar tal como se publicó, DQ o No disponible', () => {
    expect(formatPlace({ place: '1', isDq: false }, es)).toBe('1')
    expect(formatPlace({ place: '9-12', isDq: false }, es)).toBe('9-12')
    expect(formatPlace({ place: 'DQ', isDq: true }, es)).toBe('DQ')
    expect(formatPlace({ place: null, isDq: false }, es)).toBe('No disponible')
  })

  it('gamertag de la final junto al actual, o uno solo si coinciden', () => {
    expect(formatRosterGamertag({ gamertagAtFinal: 'Simplicity', currentGamertag: 'Simp' })).toEqual(['Simplicity', 'Simp'])
    expect(formatRosterGamertag({ gamertagAtFinal: 'Simp', currentGamertag: 'Simp' })).toEqual(['Simp'])
    expect(formatRosterGamertag({ gamertagAtFinal: null, currentGamertag: 'Simp' })).toEqual(['Simp'])
  })

  it('dato ausente del historial', () => {
    expect(formatHistoryField(null, es)).toBe('No disponible')
    expect(formatHistoryField(0, es)).toBe('0')
    expect(formatHistoryField(800000, es)).toBe('800000')
  })
})

describe('jugadores (T-064 · RF-23 a RF-25, RF-68, RF-71, RF-107, RF-108)', () => {
  it('edad exacta, rango o No disponible; nunca una fecha', () => {
    expect(formatAge({ min: 24, max: 24 }, es)).toBe('24')
    expect(formatAge({ min: 24, max: 25 }, es)).toBe('24–25')
    expect(formatAge(null, en)).toBe('Not available')
  })

  it('dato personal ausente', () => {
    expect(formatPersonalField('Chris Lehr', es)).toBe('Chris Lehr')
    expect(formatPersonalField(null, es)).toBe('No disponible')
  })

  it('rol o Sin rol', () => {
    expect(formatRole('AR', es)).toBe('AR')
    expect(formatRole(null, es)).toBe('Sin rol')
    expect(formatRole(null, en)).toBe('No role')
  })

  it('equipo o Agente libre', () => {
    expect(formatTeam({ isFreeAgent: true }, 'FaZe VGS', es)).toBe('Agente libre')
    expect(formatTeam({ isFreeAgent: false }, 'FaZe VGS', es)).toBe('FaZe VGS')
    expect(formatTeam({ isFreeAgent: false }, null, es)).toBe('No disponible')
  })

  it('fuera del historial se usa el gamertag actual', () => {
    expect(currentGamertag({ currentGamertag: 'Simp', previousGamertags: ['Simplicity'] })).toBe('Simp')
  })
})

describe('partidos: textos (T-065 · RF-70, RF-85, RF-86, RF-90, RF-135)', () => {
  it('fecha y hora en la zona del dispositivo', () => {
    const iso = '2026-07-19T22:00:00Z'
    expect(formatMatchDateTime(iso, 'es', { timeZone: 'America/Los_Angeles' })).toBe('19 de julio de 2026 a las 15:00')
    expect(formatMatchDateTime(iso, 'es', { timeZone: 'Europe/Madrid' })).toBe('20 de julio de 2026 a las 0:00')
    expect(formatMatchDateTime(null, 'es')).toBeNull()
  })

  it('equipo conocido, por decidir con origen o sin origen', () => {
    const known = { franchiseId: 'f1', identity: { shortName: 'FaZe VGS' }, origin: null }
    const winner = { franchiseId: null, identity: null, origin: { matchId: 'm1', outcome: 'winner' } }
    const loser = { franchiseId: null, identity: null, origin: { matchId: 'm2', outcome: 'loser' } }
    const unknown = { franchiseId: null, identity: null, origin: null }
    const describe = (id) => ({ m1: 'Final de ganadores', m2: 'Semifinal 2' })[id]
    expect(formatSlot(known, es, describe)).toBe('FaZe VGS')
    expect(formatSlot(winner, es, describe)).toBe('Ganador de Final de ganadores')
    expect(formatSlot(loser, en, describe)).toBe('Loser of Semifinal 2')
    expect(formatSlot(unknown, es, describe)).toBe('Por definir')
  })

  it('marcador en vivo ausente', () => {
    expect(formatLiveMapScore({ mode: 'Hardpoint', score: [120, 80] }, es)).toBe('120–80')
    expect(formatLiveMapScore({ mode: null, score: null }, es)).toBe('No disponible')
    expect(formatLiveMapScore(null, es)).toBe('No disponible')
  })

  it('fase traducida o No disponible', () => {
    expect(formatPhase('grand_final', es)).toBe('gran final')
    expect(formatPhase('winners_bracket', en)).toBe('winners bracket')
    expect(formatPhase(null, es)).toBe('No disponible')
  })
})

const stat = (overrides = {}) => ({
  kills: 10, deaths: 9, kd: 1.11, damage: null, assists: null, hillTime: null, contestedHillTime: null,
  firstBloods: null, firstDeaths: null, plants: null, defuses: null, zoneCaptures: null, overloads: null,
  ...overrides,
})
const empty = () => stat({ kills: null, deaths: null, kd: null })
const playedMap = (stats) => ({ position: 1, mode: 'Hardpoint', mapName: 'Vault', played: true, score: [250, 200], stats })

describe('partidos: mapas y estadísticas (T-066 · RF-46 a RF-48, RF-72, RF-94)', () => {
  it('mapas no jugados con su etiqueta y sin marcador', () => {
    const maps = displayMaps([
      { position: 2, mode: 'Search and Destroy', mapName: 'Sake', played: false, score: null, stats: [] },
      playedMap([]),
    ], es)
    expect(maps.map((m) => m.position)).toEqual([1, 2])
    expect(maps[0]).toMatchObject({ scoreText: '250–200', notPlayedLabel: null })
    expect(maps[1]).toMatchObject({ scoreText: null, notPlayedLabel: 'No jugado', mapName: 'Sake' })
  })

  it('una estadística ausente es No disponible y 0 se muestra', () => {
    expect(formatStat(0, es)).toBe('0')
    expect(formatStat(1.33, es)).toBe('1.33')
    expect(formatStat(null, es)).toBe('No disponible')
  })

  it('aviso de estadísticas pendientes', () => {
    const finished = (maps) => ({ status: 'finished', maps })
    expect(needsStatsPendingNotice(finished([playedMap([stat(), empty()])]))).toBe(true)
    expect(needsStatsPendingNotice(finished([playedMap([stat({ damage: null })])]))).toBe(false)
    expect(needsStatsPendingNotice(finished([playedMap([])]))).toBe(true)
    expect(needsStatsPendingNotice(finished([playedMap([stat(), stat()])]))).toBe(false)
    expect(needsStatsPendingNotice(finished([]))).toBe(false)
    expect(needsStatsPendingNotice({ status: 'live', maps: [playedMap([empty()])] })).toBe(false)
    expect(needsStatsPendingNotice(finished([{ ...playedMap([]), played: false }]))).toBe(false)
  })
})

describe('correcciones y tabla (T-067 · RF-51, RF-99)', () => {
  it('campo corregido', () => {
    expect(isCorrected({ correctedFields: ['score_2'] }, 'score_2')).toBe(true)
    expect(isCorrected({ correctedFields: [] }, 'score_2')).toBe(false)
    expect(leagueText(es, 'corrected')).toBe('Corregido')
  })

  it('tabla no disponible si no hay filas o ningún equipo tiene puntos', () => {
    expect(isStandingsAvailable([])).toBe(false)
    expect(isStandingsAvailable([{ points: null }, { points: 0 }])).toBe(false)
    expect(isStandingsAvailable([{ points: 0 }, { points: 30 }])).toBe(true)
    expect(standingsUnavailableText(es)).toBe('La tabla de posiciones todavía no está disponible')
  })
})

const identity = (overrides) => ({
  shortName: 'Equipo', abbreviation: 'EQP', logoUrl: null, primaryColor: null, secondaryColor: null,
  validFrom: '2025-01-01T00:00:00Z', ...overrides,
})

describe('escudo de equipo (T-068 · RF-14, RF-15, RF-118, RF-127, RF-128)', () => {
  const old = identity({ logoUrl: 'https://x.test/old.png', validFrom: '2019-01-01T00:00:00Z' })

  it('con logo propio se usa ese logo', () => {
    const own = identity({ logoUrl: 'https://x.test/own.png' })
    expect(resolveTeamBadge(own, [old, own])).toEqual({ kind: 'logo', src: 'https://x.test/own.png' })
  })

  it('sin logo se usa el de la identidad más reciente', () => {
    const recent = identity({ logoUrl: 'https://x.test/new.png', validFrom: '2026-01-01T00:00:00Z' })
    const noLogo = identity({ validFrom: '2020-01-01T00:00:00Z' })
    expect(resolveTeamBadge(noLogo, [recent, noLogo])).toEqual({ kind: 'logo', src: 'https://x.test/new.png' })
  })

  it('sin logo propio ni en la más reciente: abreviatura sobre el color primario, aunque una antigua tenga logo', () => {
    const recent = identity({ primaryColor: '#f5d90a', validFrom: '2026-01-01T00:00:00Z' })
    const badge = resolveTeamBadge(recent, [old, recent])
    expect(badge).toEqual({ kind: 'abbreviation', text: 'EQP', background: '#f5d90a', foreground: '#000000' })
  })

  it('sin color primario (o con un color no válido) se usa el color neutro', () => {
    for (const primaryColor of [null, 'rojo']) {
      const badge = resolveTeamBadge(identity({ primaryColor }), [])
      expect(badge.background).toBe(colors['team-neutral'])
      expect(badge.foreground).toBe(bestTextColor(colors['team-neutral']))
    }
  })

  it('sin abreviatura se usa el nombre corto', () => {
    expect(resolveTeamBadge(identity({ abbreviation: null, shortName: 'DAL Empire' }), []).text).toBe('DAL Empire')
  })

  it('texto blanco o negro, el de más contraste, y nunca por debajo de 4,5:1', () => {
    expect(bestTextColor('#000000')).toBe('#ffffff')
    expect(bestTextColor('#ffffff')).toBe('#000000')
    let seed = 42
    const random = () => ((seed = (seed * 1103515245 + 12345) % 2 ** 31) / 2 ** 31)
    for (let i = 0; i < 1000; i += 1) {
      const hex = `#${Math.floor(random() * 0xffffff).toString(16).padStart(6, '0')}`
      const badge = resolveTeamBadge(identity({ primaryColor: hex }), [])
      expect(contrastRatio(badge.foreground, badge.background)).toBeGreaterThanOrEqual(4.5)
    }
  })
})
