import { describe, expect, it } from 'vitest'
import { nextSortState } from './sortCycle.js'

describe('ciclo de orden de una columna (spec 004, RF-3 a RF-5)', () => {
  it('desde el orden por defecto, una columna empieza de mejor a peor', () => {
    expect(nextSortState(null, 'points')).toEqual({ columnId: 'points', direction: 'best' })
  })

  it('pulsaciones seguidas en la misma columna: mejor → peor → orden por defecto → mejor', () => {
    let state = null
    const seen = []
    for (let i = 0; i < 4; i += 1) {
      state = nextSortState(state, 'points')
      seen.push(state)
    }
    expect(seen).toEqual([
      { columnId: 'points', direction: 'best' },
      { columnId: 'points', direction: 'worst' },
      null,
      { columnId: 'points', direction: 'best' },
    ])
  })

  it('otra columna empieza de mejor a peor, sea cual sea el sentido de la anterior', () => {
    expect(nextSortState({ columnId: 'points', direction: 'best' }, 'maps')).toEqual({
      columnId: 'maps',
      direction: 'best',
    })
    expect(nextSortState({ columnId: 'points', direction: 'worst' }, 'maps')).toEqual({
      columnId: 'maps',
      direction: 'best',
    })
  })

  it('no modifica el estado que recibe', () => {
    const state = Object.freeze({ columnId: 'points', direction: 'best' })
    expect(() => nextSortState(state, 'points')).not.toThrow()
    expect(state).toEqual({ columnId: 'points', direction: 'best' })
  })
})
