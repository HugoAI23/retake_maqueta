import { act, fireEvent, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../test/renderWithProviders.jsx'
import { TruncatedName } from './TruncatedName.jsx'

const NAME = 'Los Angeles Thieves'

/** jsdom no maqueta: se simula si el texto cabe o no en su caja. */
function mockFit(fits) {
  vi.spyOn(HTMLElement.prototype, 'clientWidth', 'get').mockReturnValue(100)
  vi.spyOn(HTMLElement.prototype, 'scrollWidth', 'get').mockReturnValue(fits ? 100 : 180)
}

const nameElement = () => screen.getByText(NAME, { selector: '[data-truncated-name]' })

describe('nombre recortado (spec 004, RF-17, RF-17a, RF-17b; plan §2.6, H-2)', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('si el nombre cabe, es texto normal: sin foco ni burbuja', () => {
    mockFit(true)
    renderWithProviders(<TruncatedName text={NAME} />)
    expect(nameElement()).not.toHaveAttribute('tabindex')
    fireEvent.focus(nameElement())
    fireEvent.pointerEnter(nameElement())
    expect(screen.queryByRole('tooltip')).toBeNull()
  })

  it('si no cabe, se recorta, recibe el foco y el foco abre la burbuja asociada', async () => {
    mockFit(false)
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    renderWithProviders(<TruncatedName text={NAME} />)
    expect(nameElement()).toHaveClass('truncate')
    expect(nameElement()).toHaveAttribute('tabindex', '0')

    await user.tab()
    expect(nameElement()).toHaveFocus()
    const tooltip = screen.getByRole('tooltip')
    expect(tooltip).toHaveTextContent(NAME)
    expect(nameElement()).toHaveAttribute('aria-describedby', tooltip.id)

    await user.tab()
    expect(screen.queryByRole('tooltip')).toBeNull()
  })

  it('se abre con el puntero y sigue abierta al pasar el puntero a la burbuja', async () => {
    mockFit(false)
    renderWithProviders(<TruncatedName text={NAME} />)
    fireEvent.pointerEnter(nameElement())
    const tooltip = screen.getByRole('tooltip')

    fireEvent.pointerLeave(nameElement())
    fireEvent.pointerEnter(tooltip)
    act(() => vi.advanceTimersByTime(1000))
    expect(screen.getByRole('tooltip')).toBeInTheDocument()

    fireEvent.pointerLeave(tooltip)
    act(() => vi.advanceTimersByTime(1000))
    expect(screen.queryByRole('tooltip')).toBeNull()
  })

  it('sigue abierta mientras el foco esté en el nombre, aunque se vaya el puntero', () => {
    mockFit(false)
    renderWithProviders(<TruncatedName text={NAME} />)
    act(() => nameElement().focus())
    fireEvent.pointerEnter(nameElement())
    fireEvent.pointerLeave(nameElement())
    act(() => vi.advanceTimersByTime(1000))
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
  })

  it('se abre con un toque y se cierra con Escape sin mover el foco ni el puntero', async () => {
    mockFit(false)
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    renderWithProviders(<TruncatedName text={NAME} />)
    await user.click(nameElement())
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    expect(nameElement()).toHaveFocus()

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('tooltip')).toBeNull()
    expect(nameElement()).toHaveFocus()
  })

  it('un toque fuera la cierra', async () => {
    mockFit(false)
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    renderWithProviders(
      <div>
        <TruncatedName text={NAME} />
        <p>Fuera</p>
      </div>,
    )
    await user.click(nameElement())
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    await user.click(screen.getByText('Fuera'))
    // El puntero también sale del nombre: pasa el margen para llegar a la burbuja.
    act(() => vi.advanceTimersByTime(1000))
    expect(screen.queryByRole('tooltip')).toBeNull()
  })

  it('no se sale de la pantalla a 320 px', () => {
    mockFit(false)
    const originalWidth = window.innerWidth
    window.innerWidth = 320
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function rect() {
      // El nombre está pegado al borde derecho; la burbuja mide 200 px.
      const isTooltip = this.getAttribute('role') === 'tooltip'
      const box = isTooltip ? { left: 0, top: 0, width: 200, height: 30 } : { left: 250, top: 100, width: 60, height: 20 }
      return { ...box, right: box.left + box.width, bottom: box.top + box.height, x: box.left, y: box.top, toJSON() {} }
    })
    try {
      renderWithProviders(<TruncatedName text={NAME} />)
      fireEvent.pointerEnter(nameElement())
      const tooltip = screen.getByRole('tooltip')
      const left = parseFloat(tooltip.style.left)
      expect(left).toBeGreaterThanOrEqual(0)
      expect(left + 200).toBeLessThanOrEqual(320)
      expect(parseFloat(tooltip.style.top)).toBeGreaterThanOrEqual(120)
    } finally {
      window.innerWidth = originalWidth
    }
  })
})
