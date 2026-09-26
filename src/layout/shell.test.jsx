import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { renderApp } from '../test/renderApp.jsx'
import { renderWithProviders } from '../test/renderWithProviders.jsx'
import { Logo } from '../shared/Logo.jsx'
import { fireEvent } from '@testing-library/react'

// Secciones que aún no tienen su spec de contenido (Posiciones la tiene desde la spec 004).
const SECTION_PATHS = ['/matches', '/teams', '/players', '/tournaments', '/news', '/ml-models']

describe('marco común (RF-1, RF-3)', () => {
  it.each(['/', '/players', '/no-existe'])('en %s: cinta, menú, contenido y pie en ese orden', (route) => {
    const { container } = renderApp(route)
    const ticker = screen.getByTestId('score-ticker')
    const header = container.querySelector('header')
    const main = screen.getByRole('main')
    const footer = screen.getByRole('contentinfo')
    const order = [ticker, header, main, footer]
    for (let i = 0; i < order.length - 1; i += 1) {
      expect(order[i].compareDocumentPosition(order[i + 1]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    }
    // Nada fijo al hacer scroll.
    expect(header.className).not.toMatch(/\b(fixed|sticky)\b/)
    expect(ticker.className).not.toMatch(/\b(fixed|sticky)\b/)
  })
})

describe('rutas (RF-26, RF-27, RF-37, RF-54, RF-55)', () => {
  it.each(SECTION_PATHS)('%s muestra "Próximamente" con el nombre de la sección', (path) => {
    renderApp(path)
    const main = screen.getByRole('main')
    expect(within(main).getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(within(main).getByText('Próximamente')).toBeInTheDocument()
  })

  it('/standings pinta la sección Posiciones dentro del marco, sin "Próximamente" (spec 004, RF-52)', () => {
    renderApp('/standings')
    const main = screen.getByRole('main')
    expect(within(main).getByTestId('standings-page')).toBeInTheDocument()
    expect(within(main).getByRole('heading', { level: 1, name: 'Posiciones' })).toBeInTheDocument()
    expect(within(main).queryByText('Próximamente')).toBeNull()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  it('una dirección inventada muestra "Página no encontrada" con enlace a Inicio y sin reflejar la dirección', () => {
    renderApp('/<script>alert(1)</script>')
    const main = screen.getByRole('main')
    expect(within(main).getByRole('heading', { name: 'Página no encontrada' })).toBeInTheDocument()
    expect(within(main).getByRole('link', { name: 'Volver a Inicio' })).toHaveAttribute('href', '/')
    expect(main.textContent).not.toContain('script')
  })
})

describe('título de la pestaña (RF-30, RF-31)', () => {
  it('Inicio: "Retake"', () => {
    renderApp('/')
    expect(document.title).toBe('Retake')
  })

  it('sección: "<sección> · Retake" en el idioma activo', () => {
    renderApp('/players', { locale: 'en' })
    expect(document.title).toBe('Players · Retake')
  })

  it('404: "Página no encontrada · Retake" y cambia con el idioma', async () => {
    renderApp('/nada')
    expect(document.title).toBe('Página no encontrada · Retake')
    await userEvent.click(screen.getAllByRole('button', { name: 'English' })[0])
    expect(document.title).toBe('Page not found · Retake')
  })
})

describe('Logo (RF-11 a RF-13)', () => {
  it('aparece en el menú y enlaza a Inicio', () => {
    renderApp('/players')
    const link = screen.getByRole('link', { name: 'Retake, ir a Inicio' })
    expect(link).toHaveAttribute('href', '/')
  })

  it('si la imagen falla, muestra el texto "Retake" sin perder el enlace', () => {
    renderWithProviders(<Logo src="/no-existe.svg" />)
    const link = screen.getByRole('link', { name: 'Retake, ir a Inicio' })
    fireEvent.error(link.querySelector('img'))
    expect(link).toHaveTextContent('Retake')
    expect(link.querySelector('img')).toBeNull()
    expect(link).toHaveAttribute('href', '/')
  })
})

// Spec 003 (T-080, registro I-30 del plan de la 003): el año ya no es un valor fijo, sale de
// /api/season/current; estas pruebas simulan esa respuesta.
function seasonApi(year) {
  vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify({ year }), {
    status: 200, headers: { 'Content-Type': 'application/json' },
  }))))
}

describe('pie de página (RF-56 a RF-58)', () => {
  it('muestra nombre, aviso escolar y año de temporada', async () => {
    seasonApi(2026)
    renderApp('/')
    const footer = screen.getByRole('contentinfo')
    expect(footer).toHaveTextContent('Retake')
    expect(footer).toHaveTextContent('Proyecto escolar sin afiliación oficial con la Call of Duty League.')
    expect(await within(footer).findByText('Temporada 2026')).toBeInTheDocument()
  })

  it('en inglés', async () => {
    seasonApi(2026)
    renderApp('/', { locale: 'en' })
    expect(await within(screen.getByRole('contentinfo')).findByText('2026 season')).toBeInTheDocument()
  })
})

describe('inicio (RF-32 a RF-36, RF-38)', () => {
  it('reserva los tres huecos con su nombre y "Próximamente", en orden spotlight, noticias, cuadrícula', () => {
    renderApp('/')
    const main = screen.getByRole('main')
    const headings = within(main).getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(headings).toEqual(['Spotlight', 'Noticias', 'Próximos partidos'])
    expect(screen.getByTestId('slot-spotlight').className).toContain('lg:col-span-2')
    expect(screen.getByTestId('slot-matchGrid').className).toContain('lg:col-span-3')
  })

  it('la cinta muestra su nombre y "Próximamente" sin cargar nada', () => {
    renderApp('/')
    const ticker = screen.getByTestId('score-ticker')
    expect(ticker).toHaveTextContent('Cinta de marcadores')
    expect(ticker).toHaveTextContent('Próximamente')
    expect(within(ticker).queryByRole('status')).toBeNull()
  })
})
