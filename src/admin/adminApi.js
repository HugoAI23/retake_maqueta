/**
 * Cliente de la API de administración `/api/admin` (spec 003: RF-100 a RF-154; plan §3.4, D-11).
 *
 * - La sesión viaja en una cookie `HttpOnly` del mismo origen: el código no la ve nunca.
 * - Toda petición que cambia algo lleva la cabecera `X-Retake-Admin: 1` (D-11).
 * - Un 401 es una sesión caducada o cerrada: la página vuelve a la pantalla de acceso (RF-137).
 */

const BASE_URL = '/api/admin'

export class AdminApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'AdminApiError'
    this.status = status
  }
}
/** Sin sesión válida (401). */
export class AdminAuthError extends AdminApiError {}
/** Origen bloqueado por demasiados intentos fallidos (429, RF-127 a RF-129). */
export class AdminBlockedError extends AdminApiError {}

async function request(path, { method = 'GET', body } = {}) {
  const headers = { Accept: 'application/json' }
  if (method !== 'GET') {
    headers['X-Retake-Admin'] = '1'
    if (body !== undefined) headers['Content-Type'] = 'application/json'
  }
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method, headers, credentials: 'same-origin', body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (error) {
    throw new AdminApiError(`No se pudo contactar con la API (${path}): ${error.message}`, 0)
  }
  if (response.status === 401) throw new AdminAuthError('Sesión no válida o caducada.', 401)
  if (response.status === 429) throw new AdminBlockedError('Origen bloqueado.', 429)
  if (!response.ok) throw new AdminApiError(`La API respondió ${response.status} en ${path}`, response.status)
  return response.status === 204 ? null : response.json()
}

export const login = (username, password) => request('/login', { method: 'POST', body: { username, password } })
export const logout = () => request('/logout', { method: 'POST' })
export const me = () => request('/me')
export const getSources = () => request('/sources')
export const refreshSource = (source) => request(`/sources/${encodeURIComponent(source)}/refresh`, { method: 'POST' })
export const getRequest = (id) => request(`/requests/${encodeURIComponent(id)}`)
export const getLog = ({ source, page = 1, pageSize = 50 } = {}) => {
  const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
  if (source) params.set('source', source)
  return request(`/log?${params}`)
}
export const getSummaries = () => request('/summaries')
