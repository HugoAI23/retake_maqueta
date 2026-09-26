import { screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { BASE_API, renderStandings } from './standingsTestKit.jsx'

const longDate = (iso, locale = 'es') =>
  new Intl.DateTimeFormat(locale, { dateStyle: 'long', timeStyle: 'short' }).format(new Date(iso))

describe('cabecera de Posiciones (spec 004, RF-42, RF-42a, RF-42b)', () => {
  it('título "Posiciones" y debajo "Temporada <año>"; pestaña "Posiciones · Retake"', async () => {
    renderStandings(BASE_API)
    const page = screen.getByTestId('standings-page')
    expect(within(page).getByRole('heading', { level: 1, name: 'Posiciones' })).toBeInTheDocument()
    expect(await within(page).findByText('Temporada 2026')).toBeInTheDocument()
    expect(document.title).toBe('Posiciones · Retake')
  })

  it('en inglés: "Standings", "2026 Season" y "Standings · Retake"', async () => {
    renderStandings(BASE_API, { locale: 'en' })
    expect(screen.getByRole('heading', { level: 1, name: 'Standings' })).toBeInTheDocument()
    expect(await screen.findByText('2026 Season')).toBeInTheDocument()
    expect(document.title).toBe('Standings · Retake')
  })

  it('sin temporada actual: solo el título y el texto de tabla no disponible', async () => {
    renderStandings({ ...BASE_API, season: null, standings: [] })
    expect(await screen.findByText('La tabla de posiciones todavía no está disponible')).toBeInTheDocument()
    expect(screen.queryByText(/^Temporada/)).toBeNull()
    expect(screen.queryByText(/^Actualizado/)).toBeNull()
    expect(screen.queryByRole('table')).toBeNull()
  })
})

describe('última actualización y datos sin actualizar (spec 004, RF-53a a RF-53e)', () => {
  it('bajo la temporada, el cambio más reciente de las filas', async () => {
    renderStandings(BASE_API)
    const updated = await screen.findByText(`Actualizado: ${longDate('2026-06-03T10:00:00Z')}`)
    const season = screen.getByText('Temporada 2026')
    expect(season.compareDocumentPosition(updated) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('sin tabla que mostrar, el último cambio de los dos conjuntos vigilados', async () => {
    renderStandings({ ...BASE_API, standings: [] })
    expect(await screen.findByText('La tabla de posiciones todavía no está disponible')).toBeInTheDocument()
    // El de partidos (2 de junio) es más reciente que el de la tabla (1 de junio).
    expect(await screen.findByText(`Actualizado: ${longDate('2026-06-02T09:00:00Z')}`)).toBeInTheDocument()
  })

  it('si un conjunto vigilado cambió después que las filas, manda ese cambio', async () => {
    renderStandings({
      ...BASE_API,
      freshness: { ...BASE_API.freshness, matches: { lastChangedAt: '2026-06-09T09:00:00Z', stale: false } },
    })
    // Las filas cambiaron el 3 de junio; los partidos, el 9, pero ninguno cuenta en las filas:
    // manda la fila (RF-53e: cambios de la tabla o de los partidos que cuentan).
    expect(await screen.findByText(`Actualizado: ${longDate('2026-06-03T10:00:00Z')}`)).toBeInTheDocument()
  })

  it.each(['standings', 'matches'])('si %s está sin actualizar, se avisa debajo de la última actualización', async (dataset) => {
    renderStandings({
      ...BASE_API,
      freshness: { ...BASE_API.freshness, [dataset]: { ...BASE_API.freshness[dataset], stale: true } },
    })
    const warning = await screen.findByText('Estos datos pueden no estar al día.')
    const updated = screen.getByText(/^Actualizado: /)
    expect(updated.compareDocumentPosition(warning) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('sin conjuntos sin actualizar, no hay aviso', async () => {
    renderStandings(BASE_API)
    await screen.findByRole('table')
    expect(screen.queryByText('Estos datos pueden no estar al día.')).toBeNull()
  })
})
