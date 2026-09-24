import { describe, expect, it, vi } from 'vitest'
import { AdminAuthError, AdminBlockedError, getSources, login, logout, refreshSource } from './adminApi.js'

function respond(status, body = {}) {
  const fetch = vi.fn(() => Promise.resolve(new Response(status === 204 ? null : JSON.stringify(body), { status })))
  vi.stubGlobal('fetch', fetch)
  return fetch
}

describe('cliente de la administración (T-076; RF-124, RF-137, RF-139; plan D-11)', () => {
  it('las peticiones que cambian algo llevan la cabecera propia y la cookie del mismo origen', async () => {
    const fetch = respond(200, { username: 'hugo' })
    await login('hugo', 'secreto-de-prueba')
    const [url, init] = fetch.mock.calls[0]
    expect(url).toBe('/api/admin/login')
    expect(init.method).toBe('POST')
    expect(init.credentials).toBe('same-origin')
    expect(init.headers['X-Retake-Admin']).toBe('1')
    expect(JSON.parse(init.body)).toEqual({ username: 'hugo', password: 'secreto-de-prueba' })
  })

  it('nunca usa la caché del navegador (plan I-44)', async () => {
    const fetch = respond(200, [])
    await getSources()
    expect(fetch.mock.calls[0][1].cache).toBe('no-store')
  })

  it('un 401 es un error de sesión (lleva a la pantalla de acceso)', async () => {
    respond(401, { detail: 'Sesión no válida o caducada.' })
    await expect(getSources()).rejects.toBeInstanceOf(AdminAuthError)
  })

  it('un 429 es un origen bloqueado', async () => {
    respond(429, { detail: 'Demasiados intentos' })
    await expect(login('hugo', 'x')).rejects.toBeInstanceOf(AdminBlockedError)
  })

  it('pedir una actualización y cerrar sesión', async () => {
    const fetch = respond(202, { id: 'r1', status: 'pending' })
    expect(await refreshSource('bp')).toEqual({ id: 'r1', status: 'pending' })
    expect(fetch.mock.calls[0][0]).toBe('/api/admin/sources/bp/refresh')
    respond(204)
    await expect(logout()).resolves.toBeNull()
  })
})
