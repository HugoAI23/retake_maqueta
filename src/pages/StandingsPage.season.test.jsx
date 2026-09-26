import { act, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { BASE_API, renderStandings, row, stubApi } from './standingsTestKit.jsx'

const API_2027 = {
  ...BASE_API,
  season: { year: 2027, name: 'CDL 2027', startedAt: '2026-12-05T00:00:00Z' },
  standings: [
    row('f2', '[FICTICIO] Dos', 'DOS', { position: 1, points: 30 }),
    row('f1', '[FICTICIO] Uno', 'UNO', { position: 2, points: 10 }),
  ],
}

const ROLLOVER = { type: 'change', datasets: ['season', 'standings', 'matches'], changedAt: '2026-12-05T00:00:00Z' }
const sortedHeader = () => document.querySelector('th[aria-sort]')

describe('cambio de temporada con la sección abierta (spec 004, RF-51a)', () => {
  afterEach(() => window.history.replaceState(null, '', '/'))

  it('muestra el año nuevo, vuelve al orden por defecto y la tabla aparece como nueva', async () => {
    const { channel } = renderStandings(BASE_API)
    await screen.findByText('Temporada 2026')
    const before = await screen.findByRole('table')
    act(() => screen.getByRole('button', { name: /^Puntos/ }).click())
    expect(sortedHeader()).not.toBeNull()

    stubApi(API_2027)
    channel.emit(ROLLOVER)
    expect(await screen.findByText('Temporada 2027')).toBeInTheDocument()
    expect(await screen.findByRole('table', { name: 'Tabla de posiciones, temporada 2027' })).toBeInTheDocument()
    // Una tabla nueva (vuelve a hacer su entrada) y en su orden por defecto.
    expect(screen.getByRole('table')).not.toBe(before)
    expect(sortedHeader()).toBeNull()
    expect(screen.getAllByRole('rowheader').map((h) => h.querySelector('.sr-only').textContent)).toEqual([
      '[FICTICIO] Dos',
      '[FICTICIO] Uno',
    ])
    expect(document.querySelector('[aria-live]')).toBeNull()
  })

  it('si la temporada nueva aún no tiene tabla, el texto de RF-51 sin anunciarlo', async () => {
    const { channel } = renderStandings(BASE_API)
    await screen.findByRole('table')
    stubApi({ ...API_2027, standings: [] })
    channel.emit(ROLLOVER)
    expect(await screen.findByText('Temporada 2027')).toBeInTheDocument()
    expect(await screen.findByText('La tabla de posiciones todavía no está disponible')).toBeInTheDocument()
    expect(screen.queryByRole('table')).toBeNull()
    expect(document.querySelector('[aria-live]')).toBeNull()
  })

  it('la llegada del año al abrir la página no borra el orden recuperado con Atrás/Adelante (RF-11)', async () => {
    const first = renderStandings(BASE_API)
    await screen.findByText('Temporada 2026')
    await screen.findByRole('table')
    act(() => screen.getByRole('button', { name: /^Puntos/ }).click())
    first.unmount()

    // Misma entrada del historial y misma carga: como volver a la página con Atrás.
    renderStandings(BASE_API)
    await screen.findByText('Temporada 2026')
    await screen.findByRole('table')
    expect(sortedHeader()).toHaveAttribute('aria-sort', 'descending')
  })
})
