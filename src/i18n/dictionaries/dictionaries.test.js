import { describe, expect, it } from 'vitest'
import en from './en.js'
import es from './es.js'

// Aplana un diccionario anidado en una lista de pares [clave.completa, valor].
function flatten(obj, prefix = '') {
  return Object.entries(obj).flatMap(([key, value]) =>
    typeof value === 'object' && value !== null
      ? flatten(value, `${prefix}${key}.`)
      : [[`${prefix}${key}`, value]],
  )
}

const esEntries = flatten(es)
const enEntries = flatten(en)

describe('diccionarios (RF-63, RF-70)', () => {
  it('es y en tienen exactamente las mismas claves', () => {
    expect(enEntries.map(([k]) => k).sort()).toEqual(esEntries.map(([k]) => k).sort())
  })

  it.each([...esEntries, ...enEntries])('%s no está vacía', (_key, value) => {
    expect(typeof value).toBe('string')
    expect(value.trim()).not.toBe('')
  })

  it('incluye las etiquetas de estado y fase de la spec 002', () => {
    const keys = esEntries.map(([k]) => k)
    for (const key of [
      'league.matchStatus.scheduled',
      'league.matchStatus.live',
      'league.matchStatus.finished',
      'league.notAvailable',
      'league.noRole',
      'league.statsPending',
      'league.toBeDecided',
      'league.winnerOf',
      'league.loserOf',
      'league.notPlayed',
      'league.corrected',
      'league.freeAgent',
      'league.standingsUnavailable',
      'league.phase.week',
      'league.phase.group',
      'league.phase.winnersBracket',
      'league.phase.losersBracket',
      'league.phase.grandFinal',
    ]) {
      expect(keys).toContain(key)
    }
  })

  it('las fases son exactamente las cinco de la spec 002 (RF-31)', () => {
    const phases = esEntries
      .map(([k]) => k)
      .filter((k) => k.startsWith('league.phase.'))
      .sort()
    expect(phases).toEqual(
      [
        'league.phase.grandFinal',
        'league.phase.group',
        'league.phase.losersBracket',
        'league.phase.week',
        'league.phase.winnersBracket',
      ].sort(),
    )
  })

  it('las siglas DQ, SMG y AR no pasan por el diccionario (spec 002, RF-125)', () => {
    const values = [...esEntries, ...enEntries].map(([, v]) => v)
    for (const acronym of ['DQ', 'SMG', 'AR']) {
      expect(values).not.toContain(acronym)
    }
  })
})

describe('textos de las tablas y de Posiciones (spec 004, RF-40, RF-42, RF-48)', () => {
  const tableKeys = [
    'standings.season',
    'tables.columns.position',
    'tables.columns.team',
    'tables.columns.points',
    'tables.columns.series',
    'tables.columns.maps',
    'tables.columns.mapDiff',
    'tables.sort.best',
    'tables.sort.worst',
    'tables.sort.action',
    'tables.sharedPosition',
    'tables.caption.standings',
  ]
  const ofSpec004 = (entries) =>
    entries.filter(([k]) => k.startsWith('standings.') || k.startsWith('tables.'))
  // Variables {{...}} de un texto, para comprobar que las dos traducciones usan las mismas.
  const variables = (text) => [...text.matchAll(/{{(\w+)}}/g)].map(([, name]) => name).sort()

  it.each(tableKeys)('%s existe en es y en en', (key) => {
    expect(esEntries.map(([k]) => k)).toContain(key)
    expect(enEntries.map(([k]) => k)).toContain(key)
  })

  it('las claves standings.* y tables.* son las mismas en los dos diccionarios', () => {
    expect(ofSpec004(enEntries).map(([k]) => k).sort()).toEqual(
      ofSpec004(esEntries).map(([k]) => k).sort(),
    )
  })

  it.each(tableKeys)('%s usa las mismas variables en es y en en', (key) => {
    const esValue = new Map(esEntries).get(key)
    const enValue = new Map(enEntries).get(key)
    expect(variables(enValue)).toEqual(variables(esValue))
  })
})
