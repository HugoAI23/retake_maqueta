import { animate } from 'animejs'
import { createContext, useContext, useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore } from 'react'
import { colors } from '../config/designTokens.js'
import { usePageTransitionDone } from '../motion/PageTransition.jsx'
import { useReducedMotion } from '../motion/MotionProvider.jsx'

/** Duración máxima de la entrada de una tabla, desde que empieza (spec 004, RF-29). */
export const ENTRANCE_MAX_MS = 800
/** Duración de la entrada de cada fila y de sus contadores. */
const ROW_DURATION_MS = 400
/** Margen del respaldo de la entrada: si no hay fotogramas, la tabla se muestra igualmente. */
const FALLBACK_MARGIN_MS = 200
/** Separación máxima entre filas consecutivas de la entrada escalonada. */
const MAX_STAGGER_MS = 40
/** Duración del resaltado de una celda y de la recolocación de las filas (RF-32). */
export const UPDATE_MS = 300

/**
 * Retrasos de la entrada escalonada de `count` filas: la última termina en
 * ENTRANCE_MAX_MS o antes (RF-29).
 * @param {number} count
 * @returns {{ duration: number, delays: number[] }}
 */
export function planEntrance(count) {
  const stagger = count > 1 ? Math.min(MAX_STAGGER_MS, (ENTRANCE_MAX_MS - ROW_DURATION_MS) / (count - 1)) : 0
  return { duration: ROW_DURATION_MS, delays: Array.from({ length: count }, (_, i) => Math.round(i * stagger)) }
}

/**
 * Progreso (0–1) de los contadores de cada fila. Una fila sin entrada vale 1: ya muestra su valor.
 */
function createProgressStore() {
  const values = new Map()
  const listeners = new Map()
  return {
    get: (key) => (values.has(key) ? values.get(key) : 1),
    set(key, value) {
      if (values.get(key) === value) return
      values.set(key, value)
      listeners.get(key)?.forEach((listener) => listener())
    },
    subscribe(key, listener) {
      if (!listeners.has(key)) listeners.set(key, new Set())
      listeners.get(key).add(listener)
      return () => listeners.get(key).delete(listener)
    },
  }
}

/** Fila en la que está una celda, para que sus contadores sigan la entrada de su fila. */
export const RowMotionContext = createContext({ store: null, rowKey: null })

const noSubscription = () => () => {}

/** @returns {number} Progreso (0–1) de la entrada de la fila actual; 1 fuera de la entrada. */
export function useRowProgress() {
  const { store, rowKey } = useContext(RowMotionContext)
  return useSyncExternalStore(
    store ? (listener) => store.subscribe(rowKey, listener) : noSubscription,
    () => (store ? store.get(rowKey) : 1),
  )
}

/** Si una fila se ve en la ventana al aparecer la tabla (RF-28d). */
function isInViewport(element) {
  const rect = element.getBoundingClientRect()
  return rect.bottom > 0 && rect.top < window.innerHeight
}

/**
 * Animaciones de una tabla de datos (spec 004, §2.5; plan §2.5).
 *
 * Entrada:
 * - Empieza cuando termina la transición entre páginas, o al momento si no la hay (RF-28a).
 * - Solo las filas visibles al aparecer la tabla entran escalonadas y sus cifras cuentan
 *   desde 0; las demás salen ya con su valor (RF-28, RF-28d). Todo en ≤ 800 ms (RF-29).
 * - Se hace una vez por cada vez que la tabla aparece; al actualizarse no se repite (RF-28b).
 *   Si llegan datos a mitad, las cifras terminan en el valor nuevo (RF-28c): cada contador
 *   muestra su progreso aplicado al valor más reciente.
 *
 * Después de la entrada:
 * - La celda visible cuyo valor cambia se resalta y el resaltado se desvanece (RF-30).
 * - Si cambia el orden, cada fila se desplaza a su sitio con FLIP: solo `transform`, así que
 *   no cambia el scroll; la fila con el foco lo conserva (RF-31, RF-31a). Todo en ≤ 300 ms (RF-32).
 *
 * Con reducir movimiento no hay ninguna de estas animaciones (RF-33).
 *
 * @param {import('react').RefObject<HTMLTableSectionElement>} tbodyRef Cuerpo de la tabla.
 * @param {Map<string, Map<string, string>>} cellValues Valor de cada celda por fila y columna,
 *   para saber cuáles cambian (las celdas llevan `data-column-id`).
 * @returns {ReturnType<typeof createProgressStore>} Progreso de los contadores de cada fila.
 */
export function useTableMotion(tbodyRef, cellValues) {
  const reducedMotion = useReducedMotion()
  const transitionDone = usePageTransitionDone()
  const [store] = useState(createProgressStore)
  // pending: esperando para entrar · entering: en marcha · done: terminada o sin entrada.
  const phase = useRef(reducedMotion ? 'done' : 'pending')
  const enteringRows = useRef([])
  const lastTops = useRef(new Map())
  const lastValues = useRef(null)
  // Elemento con el foco dentro de la tabla antes de aplicar este pintado: si su fila se mueve,
  // el navegador puede quitarle el foco. React ya lo devuelve; esto lo asegura sin desplazar
  // la vista (RF-31a).
  const focusedBeforeCommit = useRef(null)
  const active = typeof document !== 'undefined' ? document.activeElement : null
  focusedBeforeCommit.current = tbodyRef.current?.contains(active) ? active : null

  // Al aparecer la tabla, antes de pintarla: las filas visibles esperan ocultas y con sus
  // cifras en 0 (y la copia para los lectores ya con el valor final).
  useLayoutEffect(() => {
    if (phase.current !== 'pending' || !tbodyRef.current) return
    enteringRows.current = [...tbodyRef.current.rows].filter(isInViewport)
    if (enteringRows.current.length === 0) {
      phase.current = 'done'
      return
    }
    for (const row of enteringRows.current) {
      row.style.opacity = '0'
      store.set(row.dataset.rowKey, 0)
    }
  }, [store, tbodyRef])

  useEffect(() => {
    if (phase.current !== 'pending' || !transitionDone) return undefined
    phase.current = 'entering'
    const rows = enteringRows.current
    const { duration, delays } = planEntrance(rows.length)
    let finished = 0
    const animations = rows.flatMap((row, index) => {
      const key = row.dataset.rowKey
      const counter = { progress: 0 }
      return [
        animate(row, {
          opacity: [0, 1],
          translateY: [8, 0],
          duration,
          delay: delays[index],
          ease: 'outQuad',
          onComplete: () => {
            row.style.opacity = ''
            row.style.transform = ''
            finished += 1
            if (finished === rows.length) phase.current = 'done'
          },
        }),
        animate(counter, {
          progress: [0, 1],
          duration,
          delay: delays[index],
          ease: 'outQuad',
          onUpdate: () => store.set(key, counter.progress),
          onComplete: () => store.set(key, 1),
        }),
      ]
    })
    // Respaldo: si la animación no avanza (sin fotogramas, p. ej. en una vista oculta), las
    // filas no se quedan ocultas; se muestran ya con su valor (RF-34).
    const fallback = setTimeout(() => {
      if (phase.current !== 'entering') return
      animations.forEach((animation) => animation.revert())
      for (const row of rows) {
        row.style.opacity = ''
        row.style.transform = ''
        store.set(row.dataset.rowKey, 1)
      }
      phase.current = 'done'
    }, ENTRANCE_MAX_MS + FALLBACK_MARGIN_MS)
    return () => {
      clearTimeout(fallback)
      animations.forEach((animation) => animation.revert())
      // Interrumpida (p. ej. StrictMode monta los efectos dos veces): se vuelve a preparar.
      if (phase.current === 'entering') {
        phase.current = 'pending'
        for (const row of rows) {
          row.style.opacity = '0'
          row.style.transform = ''
          store.set(row.dataset.rowKey, 0)
        }
      }
    }
  }, [transitionDone, store])

  // Tras cada pintado: foco, recolocación y resaltado.
  useLayoutEffect(() => {
    const tbody = tbodyRef.current
    if (!tbody) return
    const focused = focusedBeforeCommit.current
    if (focused?.isConnected && document.activeElement !== focused) focused.focus({ preventScroll: true })

    const rows = [...tbody.rows]
    if (!reducedMotion && phase.current === 'done') {
      for (const row of rows) {
        const before = lastTops.current.get(row.dataset.rowKey)
        const now = row.offsetTop
        if (before !== undefined && before !== now) {
          animate(row, {
            translateY: [before - now, 0],
            duration: UPDATE_MS,
            ease: 'outQuad',
            onComplete: () => {
              row.style.transform = ''
            },
          })
        }
        const previous = lastValues.current?.get(row.dataset.rowKey)
        const current = cellValues.get(row.dataset.rowKey)
        if (!previous || !current) continue
        for (const [columnId, value] of current) {
          if (!previous.has(columnId) || previous.get(columnId) === value) continue
          const cell = row.querySelector(`[data-column-id="${CSS.escape(columnId)}"]`)
          if (!cell || !isInViewport(cell)) continue
          animate(cell, {
            backgroundColor: [colors.highlight, colors.surface],
            duration: UPDATE_MS,
            ease: 'outQuad',
            onComplete: () => {
              cell.style.backgroundColor = ''
            },
          })
        }
      }
    }
    lastTops.current = new Map(rows.map((row) => [row.dataset.rowKey, row.offsetTop]))
    lastValues.current = cellValues
  })

  return store
}
