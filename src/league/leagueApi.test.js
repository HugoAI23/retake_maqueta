import { afterEach, describe, expect, it, vi } from 'vitest'
import { LeagueApiError, getChampionships, getCurrentSeason, getMatch, getPlayer, getPlayers } from './leagueApi.js'

function respond(status, body) {
  return vi.fn().mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => body })
}

afterEach(() => vi.unstubAllGlobals())

describe('leagueApi (T-061)', () => {
  it('devuelve los datos de una respuesta correcta y llama a /api', async () => {
    const fetchMock = respond(200, [{ year: 2026 }])
    vi.stubGlobal('fetch', fetchMock)
    await expect(getChampionships()).resolves.toEqual([{ year: 2026 }])
    expect(fetchMock).toHaveBeenCalledWith('/api/championships', expect.objectContaining({ headers: { Accept: 'application/json' } }))
  })

  it('nunca usa la caché del navegador: los datos en vivo deben ser los de ahora (plan I-44)', async () => {
    const fetchMock = respond(200, [])
    vi.stubGlobal('fetch', fetchMock)
    await getChampionships()
    expect(fetchMock).toHaveBeenCalledWith('/api/championships', expect.objectContaining({ cache: 'no-store' }))
  })

  it('falla con un error si el servidor responde con error', async () => {
    vi.stubGlobal('fetch', respond(500, { detail: 'x' }))
    const error = await getPlayers().catch((e) => e)
    expect(error).toBeInstanceOf(LeagueApiError)
    expect(error.status).toBe(500)
  })

  it('falla con un error si no hay red', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    const error = await getPlayers().catch((e) => e)
    expect(error).toBeInstanceOf(LeagueApiError)
    expect(error.status).toBe(0)
  })

  it('sin temporada empezada devuelve null, no un error', async () => {
    vi.stubGlobal('fetch', respond(404, { detail: 'x' }))
    await expect(getCurrentSeason()).resolves.toBeNull()
  })

  it('un detalle inexistente es un error 404 y el identificador va codificado', async () => {
    const fetchMock = respond(404, { detail: 'x' })
    vi.stubGlobal('fetch', fetchMock)
    await expect(getPlayer('a/b')).rejects.toMatchObject({ status: 404 })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/players/a%2Fb')
    await expect(getMatch('m1')).rejects.toBeInstanceOf(LeagueApiError)
  })
})
