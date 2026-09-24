import { act, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../test/renderWithProviders.jsx'
import { LiveBlock } from './LiveBlock.jsx'
import { LiveProvider } from './LiveProvider.jsx'
import { PAGE_CYCLE_MS } from './useLiveBlock.js'

function fakeChannel() {
  const listeners = new Set()
  return {
    subscribe: (fn) => (listeners.add(fn), () => listeners.delete(fn)),
    getStatus: () => ({ cutSince: null }),
    close: () => {},
    emit: (event) => listeners.forEach((fn) => fn(event)),
  }
}

function setup(load, { datasets = ['matches'], cycle = 'rest' } = {}) {
  const channel = fakeChannel()
  renderWithProviders(
    <LiveProvider channel={channel} loadFreshness={() => Promise.resolve({})}>
      <LiveBlock blockName="Partidos" load={load} datasets={datasets} cycle={cycle}
                 renderContent={(data) => <p data-testid="content">{data}</p>} />
    </LiveProvider>,
  )
  return channel
}

const flush = () => act(() => vi.advanceTimersByTimeAsync(0))

describe('bloque que se actualiza solo (T-071; RF-79 a RF-88)', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('la primera carga sigue las reglas de la 001 (esqueleto y después contenido)', async () => {
    setup(() => Promise.resolve('A'))
    expect(screen.queryByTestId('content')).toBeNull()
    await flush()
    expect(screen.getByTestId('content')).toHaveTextContent('A')
  })

  it('recarga en silencio cuando el canal avisa de un cambio de lo que muestra, sin esqueleto', async () => {
    let value = 'A'
    const load = vi.fn(() => Promise.resolve(value))
    const channel = setup(load)
    await flush()
    value = 'B'
    act(() => channel.emit({ type: 'change', datasets: ['matches'], changedAt: 'x' }))
    expect(screen.getByTestId('content')).toHaveTextContent('A') // nunca vuelve el esqueleto (RF-85)
    await flush()
    expect(screen.getByTestId('content')).toHaveTextContent('B')
  })

  it('no recarga por cambios de otros conjuntos de datos', async () => {
    const load = vi.fn(() => Promise.resolve('A'))
    const channel = setup(load)
    await flush()
    act(() => channel.emit({ type: 'change', datasets: ['players'], changedAt: 'x' }))
    await flush()
    expect(load).toHaveBeenCalledTimes(1)
  })

  it('si la recarga falla, conserva los datos sin error ni "Reintentar" y reintenta en el siguiente ciclo', async () => {
    let fail = true
    const load = vi.fn(() => (load.mock.calls.length === 1 ? Promise.resolve('A') : fail ? Promise.reject(new Error('x')) : Promise.resolve('C')))
    const channel = setup(load)
    await flush()
    act(() => channel.emit({ type: 'change', datasets: ['matches'], changedAt: 'x' }))
    await flush()
    expect(screen.getByTestId('content')).toHaveTextContent('A')
    expect(screen.queryByRole('button', { name: /Reintentar/ })).toBeNull() // RF-87
    fail = false
    await act(() => vi.advanceTimersByTimeAsync(PAGE_CYCLE_MS.rest))
    expect(screen.getByTestId('content')).toHaveTextContent('C')
  })

  it('se actualiza al menos una vez por ciclo de la página (30 s en vivo)', async () => {
    const load = vi.fn(() => Promise.resolve('A'))
    setup(load, { datasets: ['live'], cycle: 'live' })
    await flush()
    await act(() => vi.advanceTimersByTimeAsync(PAGE_CYCLE_MS.live))
    expect(load).toHaveBeenCalledTimes(2)
  })

  it('al volver a verse la pestaña recarga en 5 s como máximo', async () => {
    const load = vi.fn(() => Promise.resolve('A'))
    const channel = setup(load)
    await flush()
    act(() => channel.emit({ type: 'visible' }))
    await act(() => vi.advanceTimersByTimeAsync(5000))
    expect(load).toHaveBeenCalledTimes(2)
  })
})
