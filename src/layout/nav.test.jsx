import { act, renderHook, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useNavigate } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useNavPanelState } from '../navigation/useNavPanelState.js'
import { renderApp } from '../test/renderApp.jsx'

const ORDER_ES = ['Inicio', 'Partidos', 'Equipos', 'Jugadores', 'Torneos', 'Posiciones', 'Noticias', 'Modelos de ML']

function mainNav() {
  // La fila (desde 1024 px) es el primer <nav> "Navegación principal" dentro de la cabecera.
  return within(document.querySelector('header')).getByRole('navigation', { name: 'Navegación principal' })
}

describe('menú en fila (RF-6 a RF-10, RF-14, RF-24, RF-25, RF-80)', () => {
  it('tiene las ocho entradas en orden', () => {
    renderApp('/')
    const names = within(mainNav())
      .getAllByRole('link')
      .map((link) => link.querySelector('span').textContent)
    expect(names).toEqual(ORDER_ES)
  })

  it('solo Modelos de ML lleva fondo exclusivo, icono y etiqueta "IA"', () => {
    renderApp('/')
    const links = within(mainNav()).getAllByRole('link')
    const featured = links.filter((link) => link.className.includes('bg-ml'))
    expect(featured).toHaveLength(1)
    expect(featured[0]).toHaveTextContent('Modelos de ML')
    expect(featured[0]).toHaveTextContent('IA')
    expect(featured[0].querySelector('svg')).not.toBeNull()
    for (const link of links.filter((l) => l !== featured[0])) {
      expect(link.querySelector('svg')).toBeNull()
    }
  })

  it('marca la sección actual como activa, subrayada y como página actual', () => {
    renderApp('/players')
    const active = within(mainNav()).getByRole('link', { current: 'page' })
    expect(active).toHaveTextContent('Jugadores')
    expect(active.className).toContain('underline')
    expect(within(mainNav()).getAllByRole('link', { current: 'page' })).toHaveLength(1)
  })

  it('en la 404 no hay ninguna entrada activa', () => {
    renderApp('/players/xyz')
    expect(within(mainNav()).queryByRole('link', { current: 'page' })).toBeNull()
  })

  it('pulsar una entrada lleva a su sección', async () => {
    renderApp('/')
    await userEvent.click(within(mainNav()).getByRole('link', { name: 'Equipos' }))
    expect(within(screen.getByRole('main')).getByRole('heading', { name: 'Equipos' })).toBeInTheDocument()
  })

  it('pulsar la sección actual vuelve al principio de la página (RF-15)', async () => {
    renderApp('/teams')
    window.scrollTo.mockClear()
    await userEvent.click(within(mainNav()).getByRole('link', { name: 'Equipos' }))
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0)
  })

  it('el selector de idioma está en la cabecera (RF-59)', () => {
    renderApp('/')
    expect(within(document.querySelector('header')).getAllByRole('group', { name: 'Idioma' }).length).toBeGreaterThan(0)
  })
})

describe('menú plegado (RF-16 a RF-22, RF-82, RF-83)', () => {
  function menuButton() {
    return screen.getByRole('button', { name: /menú/ })
  }

  it('fuera del panel: logo, acceso a Modelos de ML y botón de menú con atributos accesibles', () => {
    renderApp('/')
    const button = menuButton()
    expect(button).toHaveAccessibleName('Abrir menú')
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(button).toHaveAttribute('aria-controls', 'mobile-nav-panel')
    const compact = button.parentElement
    expect(within(compact).getByRole('link', { name: /Modelos de ML/ })).toBeInTheDocument()
  })

  it('abre un panel con las ocho entradas en orden y el selector de idioma al final', async () => {
    renderApp('/')
    await userEvent.click(menuButton())
    const panel = screen.getByRole('dialog', { name: 'Menú de secciones' })
    const names = within(panel)
      .getAllByRole('link')
      .map((link) => link.querySelector('span').textContent)
    expect(names).toEqual(ORDER_ES)
    const group = within(panel).getByRole('group', { name: 'Idioma' })
    const lastLink = within(panel).getAllByRole('link').at(-1)
    expect(lastLink.compareDocumentPosition(group) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Cerrar menú', expanded: true })).toBeInTheDocument()
  })

  it('pulsar una entrada navega y cierra el panel; el foco vuelve al botón', async () => {
    renderApp('/')
    await userEvent.click(menuButton())
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('link', { name: 'Noticias' }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(within(screen.getByRole('main')).getByRole('heading', { name: 'Noticias' })).toBeInTheDocument()
    expect(document.activeElement).toBe(menuButton())
  })

  it('pulsar la entrada de la sección actual también cierra el panel', async () => {
    renderApp('/news')
    await userEvent.click(menuButton())
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('link', { name: 'Noticias' }))
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('pulsar fuera del panel lo cierra', async () => {
    renderApp('/')
    await userEvent.click(menuButton())
    await userEvent.click(screen.getByTestId('nav-backdrop'))
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('Escape cierra el panel', async () => {
    renderApp('/')
    await userEvent.click(menuButton())
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('con el panel abierto la página no se desplaza y el foco entra en el panel', async () => {
    renderApp('/')
    await userEvent.click(menuButton())
    expect(document.body.style.overflow).toBe('hidden')
    expect(screen.getByRole('dialog')).toContainElement(document.activeElement)
    await userEvent.keyboard('{Escape}')
    expect(document.body.style.overflow).toBe('')
  })

  it('cambiar de idioma con el panel abierto lo mantiene abierto (RF-64)', async () => {
    renderApp('/')
    await userEvent.click(menuButton())
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'English' }))
    expect(screen.getByRole('dialog', { name: 'Sections menu' })).toBeInTheDocument()
  })

  it('vuelve inerte el resto de la aplicación mientras está abierto', async () => {
    const root = document.createElement('div')
    root.id = 'root'
    document.body.appendChild(root)
    try {
      renderApp('/', {})
      await userEvent.click(menuButton())
      expect(root).toHaveAttribute('inert')
      await userEvent.keyboard('{Escape}')
      expect(root).not.toHaveAttribute('inert')
    } finally {
      root.remove()
    }
  })
})

describe('useNavPanelState (RF-21, RF-23, RF-28, RF-29)', () => {
  const originalMatchMedia = window.matchMedia
  afterEach(() => {
    window.matchMedia = originalMatchMedia
  })

  it('se cierra al cambiar de dirección', () => {
    const { result } = renderHook(() => ({ panel: useNavPanelState(), navigate: useNavigate() }), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    })
    act(() => result.current.panel.open())
    expect(result.current.panel.isOpen).toBe(true)
    act(() => result.current.navigate('/teams'))
    expect(result.current.panel.isOpen).toBe(false)
  })

  it('se cierra con Escape', () => {
    const { result } = renderHook(() => useNavPanelState(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    })
    act(() => result.current.open())
    act(() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' })))
    expect(result.current.isOpen).toBe(false)
  })

  it('se cierra al pasar a 1024 px o más', () => {
    let onChange
    const media = { matches: false, addEventListener: (_t, fn) => (onChange = fn), removeEventListener: vi.fn() }
    window.matchMedia = vi.fn(() => media)
    const { result } = renderHook(() => useNavPanelState(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    })
    act(() => result.current.open())
    act(() => {
      media.matches = true
      onChange()
    })
    expect(result.current.isOpen).toBe(false)
  })
})
