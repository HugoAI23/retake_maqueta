import { act, renderHook } from '@testing-library/react'
import { StrictMode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { BLOCK_LOAD_TIMEOUT_MS } from '../config/layoutConstants.js'
import { ConnectionProvider } from '../connection/ConnectionProvider.jsx'
import { blockLoaderReducer, initialBlockLoadState } from './blockLoaderMachine.js'
import { useBlockLoader } from './useBlockLoader.js'

// Operación de carga controlable desde la prueba: cada llamada crea una promesa
// que la prueba resuelve o rechaza cuando quiere.
function controllableLoad() {
  const calls = []
  const load = vi.fn(
    () =>
      new Promise((resolve, reject) => {
        calls.push({ resolve, reject })
      }),
  )
  return { load, calls }
}

const wrapper = ({ children }) => <ConnectionProvider>{children}</ConnectionProvider>

async function flush() {
  await act(async () => {})
}

describe('blockLoaderReducer: tabla de transiciones del plan §3.4', () => {
  const loading = blockLoaderReducer(initialBlockLoadState, { type: 'start', attempt: 1 })

  it('(inicio) + start → loading (RF-40)', () => {
    expect(loading).toMatchObject({ status: 'loading', attempt: 1, inFlight: true })
  })

  it('loading + resolve → ready (RF-47)', () => {
    expect(blockLoaderReducer(loading, { type: 'resolve', attempt: 1, data: 'x' })).toMatchObject({
      status: 'ready',
      data: 'x',
      inFlight: false,
    })
  })

  it('loading + reject → error failed (RF-41)', () => {
    expect(blockLoaderReducer(loading, { type: 'reject', attempt: 1 })).toMatchObject({
      status: 'error',
      errorReason: 'failed',
    })
  })

  it('loading + timeout → error timeout (RF-42)', () => {
    expect(blockLoaderReducer(loading, { type: 'timeout', attempt: 1 })).toMatchObject({
      status: 'error',
      errorReason: 'timeout',
    })
  })

  it('error + resolve de un intento anterior → ready (RF-43)', () => {
    const error = blockLoaderReducer(loading, { type: 'timeout', attempt: 1 })
    expect(blockLoaderReducer(error, { type: 'resolve', attempt: 1, data: 'tarde' })).toMatchObject({
      status: 'ready',
      data: 'tarde',
    })
  })

  it('ready + resolve tardío → se descarta', () => {
    const ready = blockLoaderReducer(loading, { type: 'resolve', attempt: 1, data: 'primero' })
    expect(blockLoaderReducer(ready, { type: 'resolve', attempt: 0, data: 'viejo' })).toBe(ready)
  })

  it('reject o timeout de un intento que no es el vigente → se ignoran', () => {
    const second = blockLoaderReducer(loading, { type: 'start', attempt: 2 })
    expect(blockLoaderReducer(second, { type: 'reject', attempt: 1 })).toBe(second)
    expect(blockLoaderReducer(second, { type: 'timeout', attempt: 1 })).toBe(second)
  })
})

describe('useBlockLoader (RF-40 a RF-47, RF-53)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('empieza cargando y pasa a ready al llegar los datos, sin aviso adicional', async () => {
    const { load, calls } = controllableLoad()
    const { result } = renderHook(() => useBlockLoader(load), { wrapper })
    expect(result.current.state.status).toBe('loading')
    await act(async () => calls[0].resolve('datos'))
    expect(result.current.state).toMatchObject({ status: 'ready', data: 'datos', errorReason: null })
  })

  it('pasa a error si la carga falla', async () => {
    const { load, calls } = controllableLoad()
    const { result } = renderHook(() => useBlockLoader(load), { wrapper })
    await act(async () => calls[0].reject(new Error('500')))
    expect(result.current.state).toMatchObject({ status: 'error', errorReason: 'failed' })
  })

  it('pasa a error por tiempo a los 15 s exactos, contados desde el inicio del intento', async () => {
    const { load } = controllableLoad()
    const { result } = renderHook(() => useBlockLoader(load), { wrapper })
    act(() => vi.advanceTimersByTime(BLOCK_LOAD_TIMEOUT_MS - 1))
    expect(result.current.state.status).toBe('loading')
    act(() => vi.advanceTimersByTime(1))
    expect(result.current.state).toMatchObject({ status: 'error', errorReason: 'timeout' })
  })

  it('los datos que llegan después del error sustituyen al aviso (RF-43)', async () => {
    const { load, calls } = controllableLoad()
    const { result } = renderHook(() => useBlockLoader(load), { wrapper })
    act(() => vi.advanceTimersByTime(BLOCK_LOAD_TIMEOUT_MS))
    expect(result.current.state.status).toBe('error')
    await act(async () => calls[0].resolve('tarde'))
    expect(result.current.state).toMatchObject({ status: 'ready', data: 'tarde' })
  })

  it('"Reintentar" inicia un intento nuevo, sin límite (RF-44, RF-45)', async () => {
    const { load, calls } = controllableLoad()
    const { result } = renderHook(() => useBlockLoader(load), { wrapper })
    for (let i = 0; i < 5; i += 1) {
      await act(async () => calls[i].reject(new Error('fallo')))
      expect(result.current.state.status).toBe('error')
      act(() => result.current.retry())
      expect(result.current.state.status).toBe('loading')
    }
    expect(load).toHaveBeenCalledTimes(6)
  })

  it('varias pulsaciones seguidas mantienen un único intento en curso (RF-46)', async () => {
    const { load, calls } = controllableLoad()
    const { result } = renderHook(() => useBlockLoader(load), { wrapper })
    await act(async () => calls[0].reject(new Error('fallo')))
    act(() => {
      result.current.retry()
      result.current.retry()
      result.current.retry()
    })
    expect(load).toHaveBeenCalledTimes(2)
  })

  it('el nuevo intento tras un error por tiempo cuenta sus propios 15 s', async () => {
    const { load } = controllableLoad()
    const { result } = renderHook(() => useBlockLoader(load), { wrapper })
    act(() => vi.advanceTimersByTime(BLOCK_LOAD_TIMEOUT_MS))
    act(() => vi.advanceTimersByTime(5000))
    act(() => result.current.retry())
    act(() => vi.advanceTimersByTime(BLOCK_LOAD_TIMEOUT_MS - 1))
    expect(result.current.state.status).toBe('loading')
    act(() => vi.advanceTimersByTime(1))
    expect(result.current.state.status).toBe('error')
  })

  it('al volver la red reintenta los bloques en error, y no los que ya cargaron (RF-53)', async () => {
    const failing = controllableLoad()
    const loaded = controllableLoad()
    const a = renderHook(() => useBlockLoader(failing.load), { wrapper })
    const b = renderHook(() => useBlockLoader(loaded.load), { wrapper })
    await act(async () => failing.calls[0].reject(new Error('sin red')))
    await act(async () => loaded.calls[0].resolve('ok'))

    act(() => window.dispatchEvent(new Event('online')))

    expect(a.result.current.state.status).toBe('loading')
    expect(failing.load).toHaveBeenCalledTimes(2)
    expect(b.result.current.state.status).toBe('ready')
    expect(loaded.load).toHaveBeenCalledTimes(1)
  })

  it('ready se mantiene aunque se pierda la red (RF-51)', async () => {
    const { load, calls } = controllableLoad()
    const { result } = renderHook(() => useBlockLoader(load), { wrapper })
    await act(async () => calls[0].resolve('datos'))
    act(() => window.dispatchEvent(new Event('offline')))
    await flush()
    expect(result.current.state).toMatchObject({ status: 'ready', data: 'datos' })
  })

  it('el doble montaje de StrictMode no provoca una segunda carga', () => {
    const { load } = controllableLoad()
    renderHook(() => useBlockLoader(load), {
      wrapper: ({ children }) => (
        <StrictMode>
          <ConnectionProvider>{children}</ConnectionProvider>
        </StrictMode>
      ),
    })
    expect(load).toHaveBeenCalledTimes(1)
  })
})
