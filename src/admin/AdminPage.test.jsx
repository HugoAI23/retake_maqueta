import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderApp } from '../test/renderApp.jsx'
import * as api from './adminApi.js'

vi.mock('./adminApi.js', async (original) => {
  const real = await original()
  return {
    ...real,
    login: vi.fn(), logout: vi.fn(), me: vi.fn(), getSources: vi.fn(), refreshSource: vi.fn(),
    getRequest: vi.fn(), getLog: vi.fn(), getSummaries: vi.fn(),
  }
})

const SOURCES = [
  { source: 'bp', lastAttemptAt: '2026-12-05T19:00:00Z', lastSuccessAt: '2026-12-05T18:00:00Z', stopped: true,
    refreshable: true, reason: null, activeRequest: null },
  { source: 'wiki', lastAttemptAt: '2026-08-01T12:00:00Z', lastSuccessAt: '2026-08-01T12:00:00Z', stopped: false,
    refreshable: false, reason: 'x', activeRequest: null },
  { source: 'cdl', lastAttemptAt: null, lastSuccessAt: null, stopped: false, refreshable: false, reason: 'x', activeRequest: null },
]
const LOG = {
  page: 1, pageSize: 50,
  runs: [{ id: 1, source: 'bp', job: 'regular', outcome: 'failure', message: '<b>503</b> Service Unavailable',
           startedAt: '2026-12-05T19:00:00Z', finishedAt: '2026-12-05T19:00:00Z', requestId: null }],
  incidents: [{ id: 1, source: 'bp', kind: 'query_failed', subject: 'regular', reason: '<script>alert(1)</script>',
                detail: null, repetitions: 4, firstAt: '2026-12-05T10:00:00Z', lastAt: '2026-12-05T19:00:00Z' }],
}

function signedIn() {
  api.me.mockResolvedValue({ username: 'hugo' })
  api.getSources.mockResolvedValue(SOURCES)
  api.getLog.mockResolvedValue(LOG)
  api.getSummaries.mockResolvedValue([{ day: '2026-12-04', content: { total_incidents: 5, total_failed_queries: 2,
                                                                      total_rejected_data: 1 }, createdAt: 'x' }])
}

describe('página de administración (T-077 a T-079)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('sin sesión pide usuario y contraseña, dentro del marco y sin entrada en el menú', async () => {
    api.me.mockRejectedValue(new api.AdminAuthError('x', 401))
    renderApp('/admin')
    expect(await screen.findByRole('heading', { name: 'Acceso de administración' })).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
    const nav = screen.getAllByRole('navigation')[0]
    expect(within(nav).queryByText(/Administración/)).toBeNull()
    expect(nav.querySelector('[aria-current="page"]')).toBeNull()
  })

  it('credenciales incorrectas: un único mensaje, sin decir cuál falla', async () => {
    api.me.mockRejectedValue(new api.AdminAuthError('x', 401))
    api.login.mockRejectedValue(new api.AdminAuthError('x', 401))
    renderApp('/admin')
    await userEvent.type(await screen.findByLabelText('Usuario'), 'nadie')
    await userEvent.type(screen.getByLabelText('Contraseña'), 'mala')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Usuario o contraseña incorrectos.')
  })

  it('origen bloqueado', async () => {
    api.me.mockRejectedValue(new api.AdminAuthError('x', 401))
    api.login.mockRejectedValue(new api.AdminBlockedError('x', 429))
    renderApp('/admin')
    await userEvent.type(await screen.findByLabelText('Usuario'), 'hugo')
    await userEvent.type(screen.getByLabelText('Contraseña'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('15 minutos')
  })

  it('si no se puede comprobar la sesión, error de bloque con "Reintentar" y no la pantalla de acceso (RF-115)', async () => {
    // Con el servidor caído no se sabe si hay sesión: pedir la contraseña haría creer que está mal.
    api.me.mockRejectedValueOnce(new api.AdminApiError('No se pudo contactar con la API (/me)', 0))
    signedIn()
    renderApp('/admin')
    const retry = await screen.findByRole('button', { name: /Reintentar/ })
    expect(screen.queryByRole('heading', { name: 'Acceso de administración' })).toBeNull()
    await userEvent.click(retry)
    expect(await screen.findByRole('heading', { name: 'Estado de las fuentes' })).toBeInTheDocument()
  })

  it('un fallo del servidor al entrar no se confunde con una contraseña incorrecta', async () => {
    api.me.mockRejectedValue(new api.AdminAuthError('x', 401))
    api.login.mockRejectedValue(new api.AdminApiError('La API respondió 502 en /login', 502))
    renderApp('/admin')
    await userEvent.type(await screen.findByLabelText('Usuario'), 'hugo')
    await userEvent.type(screen.getByLabelText('Contraseña'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('No se ha podido conectar con el servidor')
  })

  it('tras entrar muestra los paneles y "Cerrar sesión" vuelve al acceso', async () => {
    api.me.mockRejectedValueOnce(new api.AdminAuthError('x', 401))
    api.login.mockResolvedValue({ username: 'hugo' })
    signedIn()
    api.logout.mockResolvedValue(null)
    renderApp('/admin')
    await userEvent.type(await screen.findByLabelText('Usuario'), 'hugo')
    await userEvent.type(screen.getByLabelText('Contraseña'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('heading', { name: 'Estado de las fuentes' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(await screen.findByRole('heading', { name: 'Acceso de administración' })).toBeInTheDocument()
    expect(api.logout).toHaveBeenCalled()
  })

  it('estado de las fuentes: parada, última importación de la Wiki y acciones solo donde se puede', async () => {
    signedIn()
    renderApp('/admin')
    const panel = (await screen.findByRole('heading', { name: 'Estado de las fuentes' })).closest('section')
    const bp = await within(panel).findByTestId('source-bp')
    expect(bp).toHaveTextContent('Parada')
    expect(within(panel).getByTestId('source-wiki')).toHaveTextContent('Última importación')
    expect(within(panel).getByTestId('source-wiki')).not.toHaveTextContent('Parada')
    expect(within(panel).getByRole('button', { name: 'Actualizar BreakingPoint.gg' })).toBeEnabled()
    expect(within(panel).queryByRole('button', { name: /Actualizar Call of Duty Esports Wiki/ })).toBeNull()
  })

  it('pedir una actualización muestra que está en curso y después su resultado con incidencias', async () => {
    signedIn()
    api.refreshSource.mockResolvedValue({ id: 'r1', status: 'pending', result: null, incidentCount: 0, alreadyRunning: false })
    api.getRequest.mockResolvedValueOnce({ id: 'r1', status: 'running', result: null, incidentCount: 0 })
      .mockResolvedValue({ id: 'r1', status: 'done', result: 'partial', incidentCount: 3 })
    renderApp('/admin')
    await userEvent.click(await screen.findByRole('button', { name: 'Actualizar BreakingPoint.gg' }))
    expect(await screen.findByText(/En curso|Pendiente/)).toBeInTheDocument()
    expect(await screen.findByText(/Parcial/, {}, { timeout: 6000 })).toBeInTheDocument()
    expect(screen.getByText(/Incidencias: 3/)).toBeInTheDocument()
  }, 10000)

  it('una actualización ya en curso se indica', async () => {
    signedIn()
    api.refreshSource.mockResolvedValue({ id: 'r1', status: 'running', result: null, incidentCount: 0, alreadyRunning: true })
    api.getRequest.mockResolvedValue({ id: 'r1', status: 'running', result: null, incidentCount: 0 })
    renderApp('/admin')
    await userEvent.click(await screen.findByRole('button', { name: 'Actualizar BreakingPoint.gg' }))
    expect(await screen.findByText('Ya había una actualización en curso de esta fuente.')).toBeInTheDocument()
  })

  it('sin conexión, las peticiones de actualización se desactivan (RF-116)', async () => {
    signedIn()
    renderApp('/admin')
    const button = await screen.findByRole('button', { name: 'Actualizar BreakingPoint.gg' })
    act(() => {
      Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => false })
      window.dispatchEvent(new Event('offline'))
    })
    await waitFor(() => expect(button).toBeDisabled())
    Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => true })
    window.dispatchEvent(new Event('online'))
  })

  it('el registro muestra los mensajes de las fuentes como texto literal, sin traducir (RF-118, RF-119)', async () => {
    signedIn()
    renderApp('/admin')
    expect(await screen.findByText('<b>503</b> Service Unavailable')).toBeInTheDocument()
    expect(screen.getByText('<script>alert(1)</script>')).toBeInTheDocument()
    expect(document.querySelector('main b')).toBeNull()
    expect(screen.getByText(/4 veces/)).toBeInTheDocument()
  })

  it('resúmenes diarios', async () => {
    signedIn()
    renderApp('/admin')
    expect(await screen.findByText(/Incidencias: 5/)).toBeInTheDocument()
  })

  it('cada resumen detalla por fuente las consultas fallidas, los datos rechazados y cada incidencia distinta (RF-151, RF-152)', async () => {
    signedIn()
    api.getSummaries.mockResolvedValue([{ day: '2026-12-04', createdAt: 'x', content: {
      total_incidents: 5, total_failed_queries: 2, total_rejected_data: 1,
      by_source: { bp: { failed_queries: 2, rejected_data: 1, total_incidents: 5, incidents: [
        { id: 7, kind: 'query_failed', subject: 'regular', reason: '503 Service Unavailable', detail: null, repetitions: 4 },
      ] } },
    } }])
    renderApp('/admin')
    const panel = (await screen.findByRole('heading', { name: 'Resúmenes diarios' })).closest('section')
    expect(await within(panel).findByText(/BreakingPoint\.gg: consultas fallidas: 2 · datos rechazados: 1/)).toBeInTheDocument()
    expect(within(panel).getByText(/503 Service Unavailable/)).toBeInTheDocument()
    expect(within(panel).getByText(/4 veces/)).toBeInTheDocument()
    expect(within(panel).getByRole('button', { name: 'Ver en el registro' })).toBeInTheDocument()
  })

  it('si la sesión caduca, vuelve a pedir usuario y contraseña (RF-137)', async () => {
    api.me.mockResolvedValue({ username: 'hugo' })
    api.getSources.mockRejectedValue(new api.AdminAuthError('x', 401))
    api.getLog.mockResolvedValue(LOG)
    api.getSummaries.mockResolvedValue([])
    renderApp('/admin')
    expect(await screen.findByRole('heading', { name: 'Acceso de administración' })).toBeInTheDocument()
  })

  it('en inglés', async () => {
    api.me.mockRejectedValue(new api.AdminAuthError('x', 401))
    renderApp('/admin', { locale: 'en' })
    expect(await screen.findByRole('heading', { name: 'Administration sign-in' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'x' } })
  })
})
