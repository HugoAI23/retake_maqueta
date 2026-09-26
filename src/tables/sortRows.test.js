import { describe, expect, it } from 'vitest'
import { sortRows } from './sortRows.js'

// Filas ya en el orden por defecto de la sección (RF-2): los empates lo conservan (RF-7).
const rows = [
  { id: 'a', position: 1, name: 'Équipe', points: 50, series: { won: 6, lost: 2 }, diff: 8 },
  { id: 'b', position: 2, name: 'alpha', points: null, series: { won: 3, lost: 1 }, diff: -2 },
  { id: 'c', position: 3, name: 'Team 10', points: 30, series: { won: 0, lost: 0 }, diff: 0 },
  { id: 'd', position: 4, name: 'Team 2', points: 30, series: null, diff: null },
  { id: 'e', position: null, name: 'Beta', points: 70, series: { won: 9, lost: 3 }, diff: 3 },
]

const columns = [
  { id: 'position', sortKind: 'ascending', value: (r) => r.position },
  { id: 'name', sortKind: 'text', value: (r) => r.name },
  { id: 'points', sortKind: 'descending', value: (r) => r.points },
  { id: 'series', sortKind: 'record', value: (r) => r.series },
  { id: 'diff', sortKind: 'descending', value: (r) => r.diff },
  { id: 'logo', sortKind: null, value: () => null },
]

const ids = (list) => list.map((r) => r.id)
const sortBy = (columnId, direction, locale = 'es') => ids(sortRows(rows, columns, { columnId, direction }, locale))

describe('orden de las filas (spec 004, RF-2, RF-7 a RF-9)', () => {
  it('sin orden elegido devuelve el orden por defecto, sin tocar la lista original', () => {
    const result = sortRows(rows, columns, null, 'es')
    expect(ids(result)).toEqual(['a', 'b', 'c', 'd', 'e'])
    expect(result).not.toBe(rows)
  })

  it('ascending: menor es mejor; sin valor, detrás en los dos sentidos', () => {
    expect(sortBy('position', 'best')).toEqual(['a', 'b', 'c', 'd', 'e'])
    expect(sortBy('position', 'worst')).toEqual(['d', 'c', 'b', 'a', 'e'])
  })

  it('descending: mayor es mejor; los empates conservan el orden por defecto', () => {
    expect(sortBy('points', 'best')).toEqual(['e', 'a', 'c', 'd', 'b'])
    expect(sortBy('points', 'worst')).toEqual(['c', 'd', 'a', 'e', 'b'])
  })

  it('las diferencias negativas y el 0 son valores, no huecos', () => {
    expect(sortBy('diff', 'best')).toEqual(['a', 'e', 'c', 'b', 'd'])
    expect(sortBy('diff', 'worst')).toEqual(['b', 'c', 'e', 'a', 'd'])
  })

  it('record: por porcentaje de victorias y, a igualdad, más ganadas; 0–0 y no disponible, detrás', () => {
    // e 9–3 y b 3–1 tienen el 75 %: va antes e, con más ganadas. a 6–2 también es 75 %.
    expect(sortBy('series', 'best')).toEqual(['e', 'a', 'b', 'c', 'd'])
    expect(sortBy('series', 'worst')).toEqual(['b', 'a', 'e', 'c', 'd'])
  })

  it('record: un porcentaje más alto gana aunque tenga menos victorias', () => {
    const list = [
      { id: 'x', r: { won: 10, lost: 10 } },
      { id: 'y', r: { won: 2, lost: 0 } },
    ]
    const cols = [{ id: 'r', sortKind: 'record', value: (row) => row.r }]
    expect(ids(sortRows(list, cols, { columnId: 'r', direction: 'best' }, 'es'))).toEqual(['y', 'x'])
  })

  it('text: alfabético sin distinguir mayúsculas, acentos junto a su letra y números por su valor', () => {
    expect(sortBy('name', 'best')).toEqual(['b', 'e', 'a', 'd', 'c'])
    expect(sortBy('name', 'worst')).toEqual(['c', 'd', 'a', 'e', 'b'])
    expect(sortBy('name', 'best', 'en')).toEqual(['b', 'e', 'a', 'd', 'c'])
  })

  it('text: los nombres iguales salvo mayúsculas o acentos conservan el orden por defecto', () => {
    const list = [{ id: '1', n: 'Épsilon' }, { id: '2', n: 'epsilon' }, { id: '3', n: 'EPSILON' }]
    const cols = [{ id: 'n', sortKind: 'text', value: (row) => row.n }]
    expect(ids(sortRows(list, cols, { columnId: 'n', direction: 'best' }, 'es'))).toEqual(['1', '2', '3'])
    expect(ids(sortRows(list, cols, { columnId: 'n', direction: 'worst' }, 'es'))).toEqual(['1', '2', '3'])
  })

  it('una columna excluida o desconocida no reordena', () => {
    expect(sortBy('logo', 'best')).toEqual(['a', 'b', 'c', 'd', 'e'])
    expect(sortBy('nope', 'best')).toEqual(['a', 'b', 'c', 'd', 'e'])
  })

  it('es estable: el mismo resultado con los mismos datos', () => {
    expect(sortBy('points', 'best')).toEqual(sortBy('points', 'best'))
  })
})
