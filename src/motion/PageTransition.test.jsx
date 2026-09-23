import { act, render, screen } from '@testing-library/react'
import { StrictMode } from 'react'
import { MemoryRouter, useNavigate } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { PageTransition } from './PageTransition.jsx'

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

function renderInStrictMode() {
  return render(
    <StrictMode>
      <MemoryRouter initialEntries={['/']}>
        <PageTransition>
          <GoTo path="/players" />
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
