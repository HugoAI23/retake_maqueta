import { act, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { BASE_API, renderStandings, row, stubApi } from './standingsTestKit.jsx'

const UNAVAILABLE = 'La tabla de posiciones todavía no está disponible'

const points = (name) =>
  screen
    .getAllByRole('rowheader')
    .find((h) => h.textContent.includes(name))
    .closest('tr')
    .cells[2].querySelector('.sr-only').textContent

describe('estados de la sección Posiciones (spec 004, RF-24 a RF-27, RF-51, RF-53)', () => {
  it('mientras carga por primera vez, un esqueleto con forma de tabla (RF-24)', async () => {
    renderStandings(BASE_API)
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    // La primera petición ya salió con la API simulada; con esta, las siguientes no terminan.
    const skeleton = screen.getByTestId('block-skeleton')
    expect(skeleton).toHaveAttribute('data-shape', 'table')
    expect(await screen.findByRole('table')).toBeInTheDocument()
  })

  it('si falla la carga, el aviso de error con "Reintentar" de la 001, y al reintentar se recupera (RF-25)', async () => {
    const user = userEvent.setup()
    const api = { ...BASE_API, standings: new Error('caída') }
    renderStandings(api)
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('No se pudo cargar este contenido.')
    // El título y la temporada siguen ahí.
    expect(screen.getByRole('heading', { level: 1, name: 'Posiciones' })).toBeInTheDocument()

    api.standings = BASE_API.standings
    stubApi(api)
    await user.click(within(alert).getByRole('button', { name: 'Reintentar: Posiciones' }))
    expect(await screen.findByRole('table')).toBeInTheDocument()
  })

  it('en error, al volver la conexión reintenta solo (RF-25; RF-53 de la 001)', async () => {
    const api = { ...BASE_API, standings: new Error('sin red') }
    renderStandings(api)
    await screen.findByRole('alert')
    api.standings = BASE_API.standings
    stubApi(api)
    act(() => {
      window.dispatchEvent(new Event('offline'))
      window.dispatchEvent(new Event('online'))
    })
    expect(await screen.findByRole('table')).toBeInTheDocument()
  })

  it.each(['standings', 'matches'])(
    'cuando cambia %s se actualiza en silencio: sin esqueleto ni anuncios (RF-27, RF-53, RF-53b)',
    async (dataset) => {
      const api = structuredClone(BASE_API)
      const { channel } = renderStandings(api)
      await screen.findByRole('table')
      expect(points('Uno')).toBe('100')

      api.standings[0].points = 130
      stubApi(api)
      channel.emit({ type: 'change', datasets: [dataset], changedAt: '2026-06-04T00:00:00Z' })
      await vi.waitFor(() => expect(points('Uno')).toBe('130'))
      expect(screen.queryByTestId('block-skeleton')).toBeNull()
      expect(screen.queryByRole('status')).toBeNull()
      expect(screen.queryByRole('alert')).toBeNull()
      expect(document.querySelector('[aria-live]')).toBeNull()
    },
  )

  it('si una actualización falla, se conservan los datos sin aviso de error (RF-27)', async () => {
    const { channel } = renderStandings(BASE_API)
    await screen.findByRole('table')
    stubApi({ ...BASE_API, standings: new Error('caída') })
    channel.emit({ type: 'change', datasets: ['standings'], changedAt: 'x' })
    await act(async () => {})
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('sin tabla de posiciones, el texto de RF-51 en lugar de la tabla, con la última actualización', async () => {
    renderStandings({ ...BASE_API, standings: [] })
    expect(await screen.findByText(UNAVAILABLE)).toBeInTheDocument()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.getByText(/^Actualizado: /)).toBeInTheDocument()
    expect(await screen.findByText('Temporada 2026')).toBeInTheDocument()
  })

  it('con tabla pero sin puntos para ningún equipo, también el texto de RF-51', async () => {
    renderStandings({
      ...BASE_API,
      standings: [row('f1', '[FICTICIO] Uno', 'UNO', { position: 1, points: 0 }), row('f2', '[FICTICIO] Dos', 'DOS')],
    })
    expect(await screen.findByText(UNAVAILABLE)).toBeInTheDocument()
    expect(screen.queryByRole('table')).toBeNull()
  })

  it('de vacío a tener datos, la tabla aparece sin anunciarlo', async () => {
    const api = { ...BASE_API, standings: [] }
    const { channel } = renderStandings(api)
    await screen.findByText(UNAVAILABLE)
    stubApi({ ...api, standings: BASE_API.standings })
    channel.emit({ type: 'change', datasets: ['standings'], changedAt: 'x' })
    expect(await screen.findByRole('table')).toBeInTheDocument()
    expect(screen.queryByText(UNAVAILABLE)).toBeNull()
    expect(document.querySelector('[aria-live]')).toBeNull()
  })
})
