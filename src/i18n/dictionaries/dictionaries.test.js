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
      'league.phase.week',
      'league.phase.group',
      'league.phase.winnersBracket',
      'league.phase.losersBracket',
      'league.phase.final',
    ]) {
      expect(keys).toContain(key)
    }
  })
})
