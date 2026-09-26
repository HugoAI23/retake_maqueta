import { act } from '@testing-library/react'
import { vi } from 'vitest'
import { LiveProvider } from '../live/LiveProvider.jsx'
import { renderWithProviders } from '../test/renderWithProviders.jsx'
import { StandingsPage } from './StandingsPage.jsx'

/** Utilidades de las pruebas de la sección Posiciones (spec 004, F4). Datos [FICTICIO]. */

export const identity = (shortName, abbreviation, extra = {}) => ({
  id: `id-${shortName}`,
  shortName,
  abbreviation,
  logoUrl: null,
  primaryColor: '#123456',
  secondaryColor: null,
  validFrom: '2021-12-15T00:00:00Z',
  changedAt: null,
  ...extra,
})

export const row = (franchiseId, name, abbreviation, fields = {}) => ({
  franchiseId,
  identity: identity(name, abbreviation),
  position: null,
  points: null,
  series: { won: 0, lost: 0 },
  maps: { won: 0, lost: 0 },
  changedAt: '2026-06-01T10:00:00Z',
  ...fields,
})

/**
 * API simulada: cada ruta devuelve lo que diga `api` en ese momento (se puede cambiar
 * entre llamadas). Un valor `Error` hace fallar la petición; `null` en la temporada = 404.
 */
export function stubApi(api) {
  const fetchMock = vi.fn((url) => {
    const path = String(url).replace(/^.*\/api/, '')
    const key = { '/season/current': 'season', '/standings': 'standings', '/franchises': 'franchises', '/freshness': 'freshness' }[path]
    const body = key ? api[key] : undefined
    if (body instanceof Error) return Promise.reject(body)
    if (key === 'season' && body === null) return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
    if (body === undefined) return Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(structuredClone(body)) })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

/** Canal de eventos simulado de la spec 003. */
export function fakeChannel() {
  const listeners = new Set()
  return {
    subscribe: (fn) => (listeners.add(fn), () => listeners.delete(fn)),
    getStatus: () => ({ cutSince: null }),
    close: () => {},
    emit: (event) => act(() => listeners.forEach((fn) => fn(event))),
  }
}

/** Pinta la página con la API simulada y devuelve el canal. */
export function renderStandings(api, options = {}) {
  stubApi(api)
  const channel = fakeChannel()
  const view = renderWithProviders(
    <LiveProvider channel={channel}>
      <StandingsPage />
    </LiveProvider>,
    { route: '/standings', ...options },
  )
  return { ...view, channel }
}

export const BASE_API = {
  season: { year: 2026, name: 'CDL 2026', startedAt: '2025-12-05T00:00:00Z' },
  franchises: [],
  freshness: {
    standings: { lastChangedAt: '2026-06-01T09:00:00Z', stale: false },
    matches: { lastChangedAt: '2026-06-02T09:00:00Z', stale: false },
  },
  standings: [
    row('f1', '[FICTICIO] Uno', 'UNO', { position: 1, points: 100, changedAt: '2026-06-03T10:00:00Z' }),
    row('f2', '[FICTICIO] Dos', 'DOS', { position: 2, points: 80 }),
  ],
}
