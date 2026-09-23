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
