import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Cada importación nueva del módulo simula una carga nueva de la aplicación (otra marca).
async function loadModule() {
  vi.resetModules()
  return import('./useSortState.js')
}

function waitForPopState() {
  return new Promise((resolve) => window.addEventListener('popstate', resolve, { once: true }))
}

const POINTS_BEST = { columnId: 'points', direction: 'best' }

describe('orden conservado de una tabla (spec 004, RF-10, RF-11, RF-11a, RF-51a)', () => {
  let useSortState

  beforeEach(async () => {
    window.history.replaceState(null, '', '/')
    ;({ useSortState } = await loadModule())
  })

  afterEach(() => {
    window.history.replaceState(null, '', '/')
  })

  it('empieza en el orden por defecto', () => {
    const { result } = renderHook(() => useSortState('standings'))
    expect(result.current[0]).toBeNull()
  })

  it('se conserva al volver a pintar la página (datos nuevos, idioma o ancho)', () => {
    const { result, rerender } = renderHook(({ locale }) => useSortState('standings'), {
      initialProps: { locale: 'es' },
    })
    act(() => result.current[1](POINTS_BEST))
    rerender({ locale: 'en' })
    expect(result.current[0]).toEqual(POINTS_BEST)
  })

  it('se recupera al volver con Atrás y con Adelante', async () => {
    window.history.pushState(null, '', '/standings')
    const first = renderHook(() => useSortState('standings'))
    act(() => first.result.current[1](POINTS_BEST))
    first.unmount()

    // Se va a otra página y se vuelve con Atrás.
    window.history.pushState(null, '', '/matches')
    let popped = waitForPopState()
    window.history.back()
    await popped
    const back = renderHook(() => useSortState('standings'))
    expect(back.result.current[0]).toEqual(POINTS_BEST)
    back.unmount()

    // Atrás otra vez (entrada sin orden) y Adelante de nuevo a Posiciones.
    popped = waitForPopState()
    window.history.back()
    await popped
    popped = waitForPopState()
    window.history.forward()
    await popped
    const forward = renderHook(() => useSortState('standings'))
    expect(forward.result.current[0]).toEqual(POINTS_BEST)
  })

  it('vuelve al orden por defecto al entrar desde el menú o un enlace (entrada nueva)', () => {
    window.history.pushState(null, '', '/standings')
    const first = renderHook(() => useSortState('standings'))
    act(() => first.result.current[1](POINTS_BEST))
    first.unmount()
    window.history.pushState(null, '', '/standings')
    const again = renderHook(() => useSortState('standings'))
    expect(again.result.current[0]).toBeNull()
  })

  it('vuelve al orden por defecto al recargar (la marca de la carga cambia)', async () => {
    const first = renderHook(() => useSortState('standings'))
    act(() => first.result.current[1](POINTS_BEST))
    first.unmount()
    const reloaded = await loadModule()
    const after = renderHook(() => reloaded.useSortState('standings'))
    expect(after.result.current[0]).toBeNull()
  })

  it('se reinicia cuando la página lo pide (cambio de temporada)', () => {
    const { result, rerender } = renderHook(({ year }) => useSortState('standings', year), {
      initialProps: { year: 2026 },
    })
    act(() => result.current[1](POINTS_BEST))
    rerender({ year: 2026 })
    expect(result.current[0]).toEqual(POINTS_BEST)
    rerender({ year: 2027 })
    expect(result.current[0]).toBeNull()
    // Y el reinicio también queda en el historial.
    const again = renderHook(() => useSortState('standings', 2027))
    expect(again.result.current[0]).toBeNull()
  })

  it('cada tabla guarda su propio orden y no borra el estado del enrutador', () => {
    window.history.replaceState({ usr: null, key: 'k1', idx: 3 }, '', '/standings')
    const a = renderHook(() => useSortState('standings'))
    const b = renderHook(() => useSortState('other'))
    act(() => a.result.current[1](POINTS_BEST))
    act(() => b.result.current[1]({ columnId: 'name', direction: 'worst' }))
    expect(window.history.state).toMatchObject({ key: 'k1', idx: 3 })
    const again = renderHook(() => useSortState('standings'))
    expect(again.result.current[0]).toEqual(POINTS_BEST)
  })

  it('en el historial solo guarda la columna, el sentido y la marca de la carga', () => {
    const { result } = renderHook(() => useSortState('standings'))
    act(() => result.current[1](POINTS_BEST))
    const saved = JSON.stringify(window.history.state)
    expect(saved).toContain('points')
    expect(Object.keys(window.history.state.retakeSort)).toEqual(['token', 'tables'])
  })
})
