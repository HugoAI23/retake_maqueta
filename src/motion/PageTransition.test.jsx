import { act, render, screen } from '@testing-library/react'
import { StrictMode } from 'react'
import { MemoryRouter, useNavigate } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { PageTransition, usePageTransitionDone } from './PageTransition.jsx'

const { animate, reduced } = vi.hoisted(() => ({
  animate: vi.fn(() => ({ revert: vi.fn() })),
  reduced: { value: false },
}))
vi.mock('animejs', () => ({ animate }))
vi.mock('./MotionProvider.jsx', () => ({ useReducedMotion: () => reduced.value }))

function GoTo({ path }) {
  const navigate = useNavigate()
  return <button onClick={() => navigate(path)}>ir</button>
}

/** Página que anota, en cada pintado, si ya terminó la transición. */
function Probe({ log }) {
  const done = usePageTransitionDone()
  log?.push(done)
  return <output data-testid="done">{String(done)}</output>
}

function renderInStrictMode(log) {
  return render(
    <StrictMode>
      <MemoryRouter initialEntries={['/']}>
        <PageTransition>
          <GoTo path="/players" />
          <Probe log={log} />
        </PageTransition>
      </MemoryRouter>
    </StrictMode>,
  )
}

describe('PageTransition (RF-85, RF-88 de la spec 001; plan de la 002, I-32)', () => {
  beforeEach(() => {
    animate.mockClear()
    reduced.value = false
  })

  it('no anima la primera carga, tampoco con StrictMode (que monta los efectos dos veces)', () => {
    renderInStrictMode()
    expect(animate).not.toHaveBeenCalled()
  })

  it('anima una vez al cambiar de página', () => {
    renderInStrictMode()
    act(() => screen.getByRole('button', { name: 'ir' }).click())
    expect(animate).toHaveBeenCalledTimes(1)
    expect(animate.mock.calls[0][0]).toBe(screen.getByTestId('page-transition'))
  })

  it('no anima con reducir movimiento', () => {
    reduced.value = true
    renderInStrictMode()
    act(() => screen.getByRole('button', { name: 'ir' }).click())
    expect(animate).not.toHaveBeenCalled()
  })
})

describe('aviso de fin de la transición (spec 004, RF-28a; plan D-4)', () => {
  beforeEach(() => {
    animate.mockClear()
    reduced.value = false
    vi.useRealTimers()
  })

  const done = () => screen.getByTestId('done').textContent

  it('en la primera carga, sin transición, avisa al momento', () => {
    renderInStrictMode()
    expect(done()).toBe('true')
  })

  it('al cambiar de página no avisa hasta que termina la transición', () => {
    const log = []
    renderInStrictMode(log)
    log.length = 0
    act(() => screen.getByRole('button', { name: 'ir' }).click())
    // Desde el primer pintado de la página nueva: la tabla no puede empezar antes.
    expect(log[0]).toBe(false)
    expect(done()).toBe('false')
    const { onComplete } = animate.mock.calls[0][1]
    act(() => onComplete())
    expect(done()).toBe('true')
  })

  it('la transición dura 200 ms, así que el aviso llega en ese tiempo', () => {
    renderInStrictMode()
    act(() => screen.getByRole('button', { name: 'ir' }).click())
    expect(animate.mock.calls[0][1].duration).toBeLessThanOrEqual(200)
  })

  it('si la animación no llega a avisar, el aviso llega igualmente al acabar su tiempo', () => {
    vi.useFakeTimers()
    renderInStrictMode()
    act(() => screen.getByRole('button', { name: 'ir' }).click())
    expect(done()).toBe('false')
    act(() => vi.advanceTimersByTime(250))
    expect(done()).toBe('true')
    vi.useRealTimers()
  })

  it('con reducir movimiento avisa al momento también al cambiar de página', () => {
    reduced.value = true
    renderInStrictMode()
    act(() => screen.getByRole('button', { name: 'ir' }).click())
    expect(done()).toBe('true')
  })

  it('fuera de PageTransition se considera terminada', () => {
    render(<Probe />)
    expect(done()).toBe('true')
  })
})
