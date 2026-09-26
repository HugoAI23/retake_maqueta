import { act, screen, within } from '@testing-library/react'
import { useState } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../test/renderWithProviders.jsx'
import { formatDiff } from './tableFormat.js'

// Anime.js simulado: se anotan las llamadas y la prueba decide cuándo avanzan.
const { calls, animate, transition } = vi.hoisted(() => {
  const calls = []
  const animate = vi.fn((targets, params) => {
    const call = { targets, params, reverted: false }
    calls.push(call)
    return {
      revert: () => {
        call.reverted = true
      },
      cancel: () => {
        call.reverted = true
      },
    }
  })
  return { calls, animate, transition: { done: true } }
})
vi.mock('animejs', () => ({ animate }))
vi.mock('../motion/PageTransition.jsx', () => ({ usePageTransitionDone: () => transition.done }))

const { DataTable } = await import('./DataTable.jsx')
const { CountUp } = await import('./CountUp.jsx')
const { ENTRANCE_MAX_MS } = await import('./useTableMotion.js')

/** Llamadas de la entrada de las filas (las que animan la opacidad). */
const rowCalls = () => calls.filter((c) => c.params.opacity)
/** Llamadas de los contadores (animan un objeto de progreso). */
const counterCalls = () => calls.filter((c) => !(c.targets instanceof Element) && 'progress' in c.params)

/** Lleva cada animación de contador a un punto (0–1) y avisa de la actualización. */
function advanceCounters(progress) {
  act(() => {
    for (const call of counterCalls()) {
      if (call.reverted) continue
      call.targets.progress = progress
      call.params.onUpdate?.()
      if (progress === 1) call.params.onComplete?.()
    }
  })
}

function finishRows() {
  act(() => {
    for (const call of rowCalls()) if (!call.reverted) call.params.onComplete?.()
  })
}

const makeRows = (count, points = (i) => 100 - i) =>
  Array.from({ length: count }, (_, i) => ({ id: `r${i}`, name: `Equipo ${i}`, points: points(i), diff: i === 0 ? -3 : 5 }))

const columns = [
  { id: 'name', header: 'Equipo', sortKind: 'text', value: (r) => r.name, render: (r) => r.name, rowHeader: true },
  {
    id: 'points',
    header: 'Puntos',
    sortKind: 'descending',
    countUp: true,
    value: (r) => r.points,
    render: (r) => <CountUp value={r.points} format={(v) => String(v)} />,
  },
  {
    id: 'diff',
    header: '±',
    sortKind: 'descending',
    countUp: true,
    value: (r) => r.diff,
    render: (r) => <CountUp value={r.diff} format={(v) => formatDiff(v, 'es')} />,
  },
]

/** Cambia los datos de la tabla montada, como una actualización automática. */
let setRows

function Table({ rows: initialRows }) {
  const [rows, updateRows] = useState(initialRows)
  const [sortState, setSortState] = useState(null)
  setRows = (next) => act(() => updateRows(next))
  return (
    <DataTable caption="Tabla" columns={columns} rows={rows} rowKey={(r) => r.id} sortState={sortState} onSortChange={setSortState} />
  )
}

/** Filas de 50 px desde y = 100 en una ventana de 600 px: se ven las 10 primeras. */
function mockRowLayout() {
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function rect() {
    // Una celda está a la altura de su fila.
    const row = this.tagName === 'TR' ? this : this.closest('tr')
    const rows = [...(row?.closest('tbody')?.children ?? [])]
    const index = rows.indexOf(row)
    const top = index >= 0 ? 100 + index * 50 : 0
    return { top, bottom: top + 50, left: 0, right: 800, width: 800, height: 50, x: 0, y: top, toJSON() {} }
  })
}

const visualText = (rowIndex, columnIndex) => {
  const row = screen.getAllByRole('row')[rowIndex + 1]
  const cell = within(row).getAllByRole('cell')[columnIndex - 1]
  return cell.querySelector('[aria-hidden="true"]').textContent
}
const readerText = (rowIndex, columnIndex) => {
  const row = screen.getAllByRole('row')[rowIndex + 1]
  const cell = within(row).getAllByRole('cell')[columnIndex - 1]
  return cell.querySelector('.sr-only').textContent
}

describe('entrada de la tabla (spec 004, RF-28 a RF-29; plan §2.5)', () => {
  let innerHeight

  beforeEach(() => {
    calls.length = 0
    animate.mockClear()
    transition.done = true
    innerHeight = window.innerHeight
    window.innerHeight = 600
    mockRowLayout()
  })

  afterEach(() => {
    window.innerHeight = innerHeight
    vi.restoreAllMocks()
  })

  it('espera al aviso de fin de la transición entre páginas (RF-28a)', () => {
    transition.done = false
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    expect(rowCalls()).toHaveLength(0)
    // Mientras espera, las filas visibles no se ven y sus cifras están en 0.
    expect(screen.getAllByRole('row')[1].style.opacity).toBe('0')
    expect(visualText(0, 1)).toBe('0')
    expect(readerText(0, 1)).toBe('100')

    transition.done = true
    setRows(makeRows(3))
    expect(rowCalls()).toHaveLength(3)
  })

  it('solo entran las filas visibles; las demás salen ya con su valor (RF-28d)', () => {
    renderWithProviders(<Table rows={makeRows(14)} />, { reducedMotion: false })
    const bodyRows = screen.getAllByRole('row').slice(1)
    expect(rowCalls().map((c) => c.targets)).toEqual(bodyRows.slice(0, 10))
    expect(counterCalls()).toHaveLength(10)
    expect(bodyRows[12].style.opacity).toBe('')
    expect(visualText(12, 1)).toBe('88')
  })

  it('las filas entran escalonadas y todo termina en 800 ms o menos (RF-29)', () => {
    renderWithProviders(<Table rows={makeRows(14)} />, { reducedMotion: false })
    const delays = rowCalls().map((c) => c.params.delay)
    expect(delays).toEqual([...delays].sort((a, b) => a - b))
    expect(new Set(delays).size).toBe(10)
    for (const call of calls) expect(call.params.delay + call.params.duration).toBeLessThanOrEqual(ENTRANCE_MAX_MS)
    expect(ENTRANCE_MAX_MS).toBeLessThanOrEqual(800)
  })

  it('las cifras cuentan desde 0 hasta su valor, con su signo (RF-28, RF-50a)', () => {
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    expect(visualText(0, 1)).toBe('0')
    expect(visualText(0, 2)).toBe('0')
    advanceCounters(0.5)
    expect(visualText(0, 1)).toBe('50')
    advanceCounters(1)
    expect(visualText(0, 1)).toBe('100')
    expect(visualText(0, 2)).toBe('−3')
    expect(visualText(1, 2)).toBe('+5')
  })

  it('al terminar, las filas quedan sin estilos propios de la entrada', () => {
    renderWithProviders(<Table rows={makeRows(2)} />, { reducedMotion: false })
    finishRows()
    const row = screen.getAllByRole('row')[1]
    expect(row.style.opacity).toBe('')
    expect(row.style.transform).toBe('')
  })

  it('no se repite al actualizarse la tabla (RF-28b)', () => {
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    advanceCounters(1)
    finishRows()
    const before = rowCalls().length
    setRows(makeRows(4, (i) => 200 - i))
    expect(rowCalls()).toHaveLength(before)
    expect(visualText(0, 1)).toBe('200')
  })

  it('se repite cada vez que la tabla aparece (Atrás/Adelante, Reintentar, de vacío a datos)', () => {
    const first = renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    first.unmount()
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    expect(rowCalls()).toHaveLength(6)
  })

  it('si llegan datos durante la entrada, las cifras terminan en el valor nuevo (RF-28c)', () => {
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    advanceCounters(0.5)
    setRows(makeRows(3, (i) => 300 - i))
    expect(rowCalls()).toHaveLength(3)
    advanceCounters(1)
    expect(visualText(0, 1)).toBe('300')
    expect(readerText(0, 1)).toBe('300')
  })

  it('si la animación no avanza (sin fotogramas), al acabar su tiempo la tabla se ve con sus valores', () => {
    vi.useFakeTimers()
    try {
      renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
      expect(screen.getAllByRole('row')[1].style.opacity).toBe('0')
      act(() => vi.advanceTimersByTime(ENTRANCE_MAX_MS + 250))
      expect(screen.getAllByRole('row').slice(1).every((r) => r.style.opacity === '' && r.style.transform === '')).toBe(true)
      expect(visualText(0, 1)).toBe('100')
      expect(calls.every((c) => c.reverted)).toBe(true)
    } finally {
      vi.useRealTimers()
    }
  })

  it('si la entrada termina a tiempo, el respaldo no hace nada', () => {
    vi.useFakeTimers()
    try {
      renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
      advanceCounters(1)
      finishRows()
      act(() => vi.advanceTimersByTime(ENTRANCE_MAX_MS + 250))
      expect(calls.some((c) => c.reverted)).toBe(false)
    } finally {
      vi.useRealTimers()
    }
  })

  it('al desmontarse a mitad, se paran sus animaciones', () => {
    const { unmount } = renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    unmount()
    expect(calls.every((c) => c.reverted)).toBe(true)
  })
})

describe('resaltado y recolocación (spec 004, RF-30 a RF-32; plan §2.5)', () => {
  let innerHeight

  beforeEach(() => {
    calls.length = 0
    animate.mockClear()
    transition.done = true
    innerHeight = window.innerHeight
    window.innerHeight = 600
    mockRowLayout()
    // Posición de cada fila en su tabla, según su sitio en el DOM (jsdom no maqueta).
    vi.spyOn(HTMLElement.prototype, 'offsetTop', 'get').mockImplementation(function offsetTop() {
      const rows = [...(this.parentElement?.children ?? [])]
      return this.tagName === 'TR' ? rows.indexOf(this) * 50 : 0
    })
  })

  afterEach(() => {
    window.innerHeight = innerHeight
    vi.restoreAllMocks()
  })

  /** Monta la tabla y deja terminada su entrada. */
  function renderSettled(rows) {
    const view = renderWithProviders(<Table rows={rows} />, { reducedMotion: false })
    advanceCounters(1)
    finishRows()
    calls.length = 0
    return view
  }

  const highlightCalls = () => calls.filter((c) => c.params.backgroundColor)
  const moveCalls = () => calls.filter((c) => c.params.translateY && !c.params.opacity)

  it('resalta la celda visible que cambia y el fondo se desvanece en ≤ 300 ms (RF-30, RF-32)', () => {
    renderSettled(makeRows(3))
    setRows(makeRows(3).map((r) => (r.id === 'r1' ? { ...r, points: 150 } : r)))
    expect(highlightCalls()).toHaveLength(1)
    const [call] = highlightCalls()
    // r1 es la segunda fila del cuerpo (la primera de todas es la cabecera).
    expect(call.targets).toBe(within(screen.getAllByRole('row')[2]).getAllByRole('cell')[0])
    expect(call.params.backgroundColor[0]).toBe('#16384a')
    expect(call.params.delay ?? 0).toBe(0)
    expect(call.params.duration).toBeLessThanOrEqual(300)
    // Sin mover la celda: solo cambia el fondo.
    expect(Object.keys(call.params).filter((k) => ['translateX', 'translateY', 'scale'].includes(k))).toEqual([])
  })

  it('no resalta las celdas que no se ven ni las que no cambian', () => {
    renderSettled(makeRows(14))
    setRows(makeRows(14).map((r) => (r.id === 'r12' ? { ...r, points: 1 } : r)))
    expect(highlightCalls()).toHaveLength(0)
  })

  it('ordenar por una columna no resalta nada: los valores no cambian', async () => {
    renderSettled(makeRows(3))
    act(() => screen.getByRole('button', { name: /Equipo/ }).click())
    act(() => screen.getByRole('button', { name: /Equipo/ }).click())
    expect(highlightCalls()).toHaveLength(0)
  })

  it('las filas se desplazan a su sitio nuevo en ≤ 300 ms al cambiar el orden (RF-31, RF-32)', () => {
    renderSettled(makeRows(3))
    // De peor a mejor en Puntos: r2, r1, r0.
    act(() => screen.getByRole('button', { name: /Puntos/ }).click())
    act(() => screen.getByRole('button', { name: /Puntos/ }).click())
    const moves = moveCalls()
    expect(moves.length).toBeGreaterThan(0)
    for (const move of moves) {
      expect(move.params.duration).toBeLessThanOrEqual(300)
      const [from, to] = move.params.translateY
      expect(to).toBe(0)
      // Empieza donde estaba antes: su posición anterior menos la nueva.
      const key = move.targets.dataset.rowKey
      const before = { r0: 0, r1: 50, r2: 100 }[key]
      expect(from).toBe(before - move.targets.offsetTop)
    }
  })

  it('también se recolocan cuando el orden cambia por datos nuevos, sin mover el scroll', () => {
    renderSettled(makeRows(3))
    const scrollBefore = [window.scrollX, window.scrollY]
    window.scrollTo.mockClear()
    setRows(makeRows(3, (i) => 100 + i * 10).reverse())
    expect(moveCalls().length).toBeGreaterThan(0)
    expect([window.scrollX, window.scrollY]).toEqual(scrollBefore)
    expect(window.scrollTo).not.toHaveBeenCalled()
  })

  it('la fila con el foco lo conserva al recolocarse (RF-31a)', () => {
    const focusColumns = [
      ...columns.slice(0, 1).map((c) => ({ ...c, render: (r) => <button type="button">{r.name}</button> })),
      ...columns.slice(1),
    ]
    function FocusTable({ rows: initialRows }) {
      const [rows, updateRows] = useState(initialRows)
      setRows = (next) => act(() => updateRows(next))
      return <DataTable caption="Tabla" columns={focusColumns} rows={rows} rowKey={(r) => r.id} sortState={null} onSortChange={() => {}} />
    }
    renderWithProviders(<FocusTable rows={makeRows(3)} />, { reducedMotion: false })
    advanceCounters(1)
    finishRows()
    const focused = screen.getByRole('button', { name: 'Equipo 0' })
    act(() => focused.focus())
    const scrollBefore = [window.scrollX, window.scrollY]
    window.scrollTo.mockClear()
    setRows([...makeRows(3)].reverse())
    expect(screen.getByRole('button', { name: 'Equipo 0' })).toHaveFocus()
    // Sin desplazar la vista.
    expect([window.scrollX, window.scrollY]).toEqual(scrollBefore)
    expect(window.scrollTo).not.toHaveBeenCalled()
  })

  it('durante la entrada no hay resaltado ni recolocación: las cifras siguen contando', () => {
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    calls.length = 0
    setRows(makeRows(3, (i) => 10 + i).map((r) => r))
    expect(highlightCalls()).toHaveLength(0)
    expect(moveCalls()).toHaveLength(0)
  })
})

describe('reducir movimiento y valor para el lector (spec 004, RF-33, RF-34; D-10)', () => {
  let innerHeight

  beforeEach(() => {
    calls.length = 0
    animate.mockClear()
    transition.done = true
    innerHeight = window.innerHeight
    window.innerHeight = 600
    mockRowLayout()
    vi.spyOn(HTMLElement.prototype, 'offsetTop', 'get').mockImplementation(function offsetTop() {
      return this.tagName === 'TR' ? [...this.parentElement.children].indexOf(this) * 50 : 0
    })
  })

  afterEach(() => {
    window.innerHeight = innerHeight
    vi.restoreAllMocks()
  })

  it('con reducir movimiento no se crea ninguna animación: ni entrada, ni resaltado, ni recolocación', () => {
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: true })
    expect(screen.getAllByRole('row')[1].style.opacity).toBe('')
    expect(visualText(0, 1)).toBe('100')
    setRows(makeRows(3, (i) => 10 + i))
    act(() => screen.getByRole('button', { name: /Puntos/ }).click())
    act(() => screen.getByRole('button', { name: /Puntos/ }).click())
    expect(animate).not.toHaveBeenCalled()
    // De peor a mejor en Puntos: primero el 10, ya con su valor final.
    expect(visualText(0, 1)).toBe('10')
  })

  it('con reducir movimiento tampoco espera a la transición entre páginas', () => {
    transition.done = false
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: true })
    expect(screen.getAllByRole('row')[1].style.opacity).toBe('')
    expect(visualText(0, 1)).toBe('100')
  })

  it('la cifra que cuenta es solo visual y el lector tiene el valor final desde el principio', () => {
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    const cell = within(screen.getAllByRole('row')[1]).getAllByRole('cell')[0]
    expect(cell.querySelector('[aria-hidden="true"]').textContent).toBe('0')
    expect(readerText(0, 1)).toBe('100')
    advanceCounters(0.3)
    expect(readerText(0, 1)).toBe('100')
    // Lo que lee el lector en la celda es solo el valor final.
    const readable = [...cell.querySelectorAll('*')].filter((n) => !n.closest('[aria-hidden="true"]') && n.children.length === 0)
    expect(readable.map((n) => n.textContent).join('')).toBe('100')
  })

  it('se puede usar la tabla durante la entrada: ordenar funciona y las filas están en el DOM', () => {
    renderWithProviders(<Table rows={makeRows(3)} />, { reducedMotion: false })
    act(() => screen.getByRole('button', { name: /Puntos/ }).click())
    act(() => screen.getByRole('button', { name: /Puntos/ }).click())
    const names = screen.getAllByRole('rowheader').map((h) => h.textContent)
    expect(names).toEqual(['Equipo 2', 'Equipo 1', 'Equipo 0'])
  })
})
