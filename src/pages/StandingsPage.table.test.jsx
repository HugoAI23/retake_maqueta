import { act, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { WIDE_MEDIA_QUERY } from '../config/layoutConstants.js'
import { BASE_API, renderStandings, row } from './standingsTestKit.jsx'

const MINUS = '−'
const DASH = '–'

/** Ventana ancha (≥ 1024 px) o estrecha. */
function mockWide(wide) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query) => ({ matches: query === WIDE_MEDIA_QUERY ? wide : false, addEventListener() {}, removeEventListener() {} })),
  )
}

const API = {
  ...BASE_API,
  franchises: [{ id: 'f9', identities: [] }], // RF-41c: no está en la tabla publicada
  standings: [
    row('f3', '[FICTICIO] Gamma', 'GAM', { position: 3, points: 50, series: { won: 5, lost: 5 }, maps: { won: 18, lost: 20 } }),
    row('f1', '[FICTICIO] Alfa', 'ALF', { position: 1, points: 120, series: { won: 9, lost: 1 }, maps: { won: 28, lost: 9 } }),
    // Empatados en la 13: por el texto que se ve (nombre ancho, abreviatura estrecha).
    row('f13a', '[FICTICIO] Zeta', 'AAA', { position: 13, points: 0, series: { won: 0, lost: 0 }, maps: { won: 0, lost: 0 } }),
    row('f13b', '[FICTICIO] Beta', 'ZZZ', { position: 13, points: 0, series: { won: 1, lost: 2 }, maps: { won: 4, lost: 6 } }),
    row('f2', '[FICTICIO] Delta', 'DEL', { position: 2, points: null, series: null, maps: null }),
    row('fx', '[FICTICIO] Sin posición', 'SNP', { position: null, points: 10, series: { won: 2, lost: 2 }, maps: { won: 7, lost: 7 } }),
  ],
}

async function table() {
  return screen.findByRole('table', { name: 'Tabla de posiciones, temporada 2026' })
}

const teamOrder = () =>
  // El nombre corto: el recortable en ancho, la copia para el lector en estrecho.
  screen.getAllByRole('rowheader').map((header) => header.querySelector('[data-truncated-name], .sr-only').textContent)

/** Texto que ve el usuario en las cifras de una fila, sin la posición ni las copias para el lector. */
function visibleCells(name) {
  const header = screen.getAllByRole('rowheader').find((h) => h.textContent.includes(name))
  return within(header.closest('tr'))
    .getAllByRole('cell')
    .slice(1)
    .map((cell) => {
      const visual = cell.querySelectorAll('[aria-hidden="true"]')
      return visual.length ? [...visual].map((n) => n.textContent).join('') : cell.textContent
    })
}

describe('tabla de posiciones (spec 004, RF-41, RF-41c, RF-43 a RF-50b)', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('columnas en orden: Pos., Equipo, Puntos, Series, Mapas y ±Mapas', async () => {
    mockWide(true)
    renderStandings(API)
    const headers = within(await table()).getAllByRole('columnheader')
    expect(headers.map((h) => h.querySelector('button span')?.textContent ?? h.textContent)).toEqual([
      'Pos.', 'Equipo', 'Puntos', 'Series', 'Mapas', '±Mapas',
    ])
  })

  it('solo las filas de la tabla publicada, sin franquicias que no están en ella (RF-41, RF-41c)', async () => {
    mockWide(true)
    renderStandings(API)
    await table()
    expect(screen.getAllByRole('rowheader')).toHaveLength(6)
  })

  it('orden por defecto: posición, empates por el texto que se ve y sin posición al final (ancho)', async () => {
    mockWide(true)
    renderStandings(API)
    await table()
    expect(teamOrder()).toEqual([
      '[FICTICIO] Alfa', '[FICTICIO] Delta', '[FICTICIO] Gamma', '[FICTICIO] Beta', '[FICTICIO] Zeta', '[FICTICIO] Sin posición',
    ])
  })

  it('por debajo de 1024 px los empates van por la abreviatura, que es lo que se ve (RF-47)', async () => {
    mockWide(false)
    renderStandings(API)
    await table()
    // AAA (Zeta) antes que ZZZ (Beta).
    expect(teamOrder().slice(3, 5)).toEqual(['[FICTICIO] Zeta', '[FICTICIO] Beta'])
  })

  it('cifras: balances "g–p", ±Mapas con signo y "No disponible" donde falta', async () => {
    mockWide(true)
    renderStandings(API)
    await table()
    expect(visibleCells('Alfa')).toEqual(['120', `9${DASH}1`, `28${DASH}9`, '+19'])
    expect(visibleCells('Gamma')).toEqual(['50', `5${DASH}5`, `18${DASH}20`, `${MINUS}2`])
    expect(visibleCells('Zeta')).toEqual(['0', `0${DASH}0`, `0${DASH}0`, '0'])
    // Sin puntos ni balance (RF-44a, RF-45a).
    expect(visibleCells('Delta')).toEqual(['No disponible', 'No disponible', 'No disponible', 'No disponible'])
    const delta = screen.getAllByRole('rowheader').find((h) => h.textContent.includes('Delta')).closest('tr')
    expect(within(delta).getAllByRole('cell')).toHaveLength(5)
    // Sin posición (RF-44a).
    const noPosition = screen.getAllByRole('rowheader').find((h) => h.textContent.includes('Sin posición')).closest('tr')
    expect(noPosition.cells[0]).toHaveTextContent('No disponible')
  })

  it('±Mapas: color positivo o negativo además del signo, y el del texto en el 0 (RF-22)', async () => {
    mockWide(true)
    renderStandings(API)
    await table()
    const diffCell = (name) => within(screen.getAllByRole('rowheader').find((h) => h.textContent.includes(name)).closest('tr')).getAllByRole('cell')[4]
    expect(diffCell('Alfa').firstElementChild).toHaveClass('text-positive')
    expect(diffCell('Gamma').firstElementChild).toHaveClass('text-danger')
    expect(diffCell('Zeta').firstElementChild).toHaveClass('text-text')
  })

  it('posición compartida: el mismo número y "compartido" para el lector (RF-48)', async () => {
    mockWide(true)
    renderStandings(API)
    await table()
    const positionCell = (name) => screen.getAllByRole('rowheader').find((h) => h.textContent.includes(name)).closest('tr').cells[0]
    for (const name of ['Zeta', 'Beta']) {
      expect(positionCell(name).querySelector('[aria-hidden="true"]').textContent).toBe('13')
      expect(positionCell(name).querySelector('.sr-only').textContent).toBe('13.º, compartido')
    }
    expect(positionCell('Alfa').textContent).toBe('1')
  })

  it('en inglés, la posición compartida se lee "13, tied"', async () => {
    mockWide(true)
    renderStandings(API, { locale: 'en' })
    await screen.findByRole('table')
    const zeta = screen.getAllByRole('rowheader').find((h) => h.textContent.includes('Zeta')).closest('tr')
    expect(zeta.cells[0].querySelector('.sr-only').textContent).toBe('13, tied')
  })

  it('reglas de mejor a peor de cada columna (RF-49)', async () => {
    mockWide(true)
    renderStandings(API)
    await table()
    const sortBy = (name) => act(() => screen.getByRole('button', { name: new RegExp(`^${name}`) }).click())

    sortBy('Puntos')
    expect(teamOrder().slice(0, 3)).toEqual(['[FICTICIO] Alfa', '[FICTICIO] Gamma', '[FICTICIO] Sin posición'])
    expect(teamOrder().at(-1)).toBe('[FICTICIO] Delta')

    // 9–1 (90 %), 5–5 y 2–2 (50 %, más ganadas antes), 1–2; detrás, en su orden por defecto,
    // no disponible (Delta, posición 2) y 0–0 (Zeta, posición 13).
    sortBy('Series')
    expect(teamOrder()).toEqual([
      '[FICTICIO] Alfa', '[FICTICIO] Gamma', '[FICTICIO] Sin posición', '[FICTICIO] Beta', '[FICTICIO] Delta', '[FICTICIO] Zeta',
    ])

    sortBy('±Mapas') // +19, 0 (Sin posición), 0 (Zeta), −2, −2; no disponible detrás
    expect(teamOrder()[0]).toBe('[FICTICIO] Alfa')
    expect(teamOrder().at(-1)).toBe('[FICTICIO] Delta')

    sortBy('Equipo')
    expect(teamOrder()).toEqual([
      '[FICTICIO] Alfa', '[FICTICIO] Beta', '[FICTICIO] Delta', '[FICTICIO] Gamma', '[FICTICIO] Sin posición', '[FICTICIO] Zeta',
    ])

    sortBy('Pos.')
    expect(teamOrder()[0]).toBe('[FICTICIO] Alfa')
    expect(teamOrder().at(-1)).toBe('[FICTICIO] Sin posición')
  })

  it('columnas fijas Pos. y Equipo; Equipo es la cabecera de fila (RF-50, RF-50b)', async () => {
    mockWide(true)
    renderStandings(API)
    const headers = within(await table()).getAllByRole('columnheader')
    expect(headers.map((h) => h.classList.contains('sticky'))).toEqual([true, true, false, false, false, false])
    expect(screen.getAllByRole('rowheader')[0].closest('tr').cells[1]).toBe(screen.getAllByRole('rowheader')[0])
  })

  it('cuentan en la entrada Puntos, Series, Mapas y ±Mapas; la posición no (RF-50a)', async () => {
    mockWide(true)
    renderStandings(API)
    await table()
    const alfa = screen.getAllByRole('rowheader').find((h) => h.textContent.includes('Alfa')).closest('tr')
    // Cada cifra que cuenta tiene su copia para el lector con el valor final (D-10).
    expect(alfa.cells[0].querySelector('.sr-only')).toBeNull()
    for (const index of [2, 3, 4, 5]) {
      expect(alfa.cells[index].querySelector('[aria-hidden="true"]')).not.toBeNull()
      expect(alfa.cells[index].querySelector('.sr-only')).not.toBeNull()
    }
    expect(alfa.cells[3].querySelector('.sr-only').textContent).toBe(`9${DASH}1`)
  })
})

describe('seguridad de la tabla (spec 004, criterio 9; plan §9)', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('un nombre con HTML de una fuente se pinta como texto, sin crear elementos', async () => {
    mockWide(true)
    const hostile = '<img src=x onerror="window.__pwned=1">[FICTICIO]'
    renderStandings({ ...BASE_API, standings: [row('f1', hostile, '<b>X</b>', { position: 1, points: 5 })] })
    await table()
    const header = screen.getAllByRole('rowheader')[0]
    expect(header.querySelector('[data-truncated-name]').textContent).toBe(hostile)
    expect(header.querySelectorAll('img')).toHaveLength(0)
    expect(header.querySelector('b')).toBeNull()
    expect(window.__pwned).toBeUndefined()
  })

  it('un color primario no válido no llega al estilo: se usa el neutro', async () => {
    mockWide(true)
    const standings = [row('f1', '[FICTICIO] Uno', 'UNO', { position: 1, points: 5 })]
    standings[0].identity.primaryColor = 'red; background-image: url(https://example.com/x)'
    renderStandings({ ...BASE_API, standings })
    await table()
    const badge = screen.getByTestId('team-badge')
    expect(badge.getAttribute('style')).not.toContain('url(')
  })
})
