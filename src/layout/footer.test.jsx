import { act, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderApp } from '../test/renderApp.jsx'
import { SEASON_REFRESH_MS } from '../live/useCurrentSeason.js'

function answer(body, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }))
}

describe('pie de página: año de la temporada (T-080; RF-74 a RF-78)', () => {
  beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }))
  afterEach(() => vi.useRealTimers())

  it('sin año hasta obtenerlo', async () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    renderApp('/')
    expect(screen.getByRole('contentinfo')).not.toHaveTextContent(/Temporada \d{4}/)
  })

  it('muestra el año que da la API', async () => {
    vi.stubGlobal('fetch', vi.fn(() => answer({ year: 2026, name: 'CDL 2026', startedAt: '2025-12-05T20:00:00Z' })))
    renderApp('/')
    expect(await screen.findByText('Temporada 2026')).toBeInTheDocument()
  })

  it('lo mantiene si después falla y lo cambia en 5 min como máximo cuando cambia la temporada', async () => {
    const fetch = vi.fn(() => answer({ year: 2026 }))
    vi.stubGlobal('fetch', fetch)
    renderApp('/')
    await screen.findByText('Temporada 2026')
    fetch.mockImplementation(() => Promise.reject(new Error('sin red')))
    await act(() => vi.advanceTimersByTimeAsync(SEASON_REFRESH_MS))
    expect(screen.getByText('Temporada 2026')).toBeInTheDocument()
    fetch.mockImplementation(() => answer({ year: 2027 }))
    await act(() => vi.advanceTimersByTimeAsync(SEASON_REFRESH_MS))
    expect(screen.getByText('Temporada 2027')).toBeInTheDocument()
  })
})

describe('pie de página: atribución de las fuentes (T-081; RF-160)', () => {
  it.each(['/', '/matches', '/no-existe', '/admin'])('aparece en %s con un enlace a cada fuente y a la licencia', (route) => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    renderApp(route)
    const footer = screen.getByRole('contentinfo')
    const links = within(footer).getAllByRole('link').map((a) => a.getAttribute('href'))
    expect(links).toEqual(expect.arrayContaining([
      'https://www.breakingpoint.gg', 'https://cod-esports.fandom.com', 'https://www.callofdutyleague.com',
      'https://creativecommons.org/licenses/by-sa/3.0/',
    ]))
  })
})
