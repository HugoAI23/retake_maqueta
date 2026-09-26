import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocale } from '../i18n/LocaleProvider.jsx'
import { nextSortState } from './sortCycle.js'
import { sortRows } from './sortRows.js'
import { RowMotionContext, useTableMotion } from './useTableMotion.js'

/**
 * Columna de una tabla de datos (plan de la 004, §3.2).
 * @template T
 * @typedef {object} Column
 * @property {string} id
 * @property {string} header Texto de la cabecera, ya traducido (RF-40).
 * @property {import('./sortRows.js').SortKind} sortKind `null` = excluida del orden.
 * @property {(row: T) => unknown} value Valor para ordenar; `null` = sin valor (RF-9).
 * @property {(row: T) => import('react').ReactNode} render
 * @property {boolean} [sticky] Columna fija al desplazar (RF-13).
 * @property {boolean} [rowHeader] Cabecera de fila para los lectores (RF-36a).
 * @property {boolean} [countUp] Cuenta desde 0 en la entrada (RF-28; lo usa la F3).
 * @property {'start' | 'end'} [align] Alineación de la columna; las cifras, al final.
 */

/**
 * Sentido de `aria-sort` según qué significa «de mejor a peor» en la columna (RF-6).
 * @param {import('./sortRows.js').SortKind} kind
 * @param {'best' | 'worst'} direction
 */
function ariaSort(kind, direction) {
  const bestIsAscending = kind === 'ascending' || kind === 'text'
  return (direction === 'best') === bestIsAscending ? 'ascending' : 'descending'
}

/** Fondo de las celdas fijas: tapa lo que pasa por debajo al desplazar. */
const STICKY = 'sticky z-10 bg-surface'

/**
 * Tabla de datos común (spec 004, §2.1 y §2.6; plan D-8, D-9).
 *
 * - `<table>` con `<caption>`, `<th scope="col">` y una cabecera de fila (RF-1, RF-36, RF-36a).
 * - Cabeceras ordenables como botones, con `aria-sort` y el sentido en texto (RF-3 a RF-6, RF-37).
 * - Desplazamiento horizontal dentro de su caja, con columnas fijas a la izquierda (RF-12, RF-13).
 *
 * El estado del orden vive fuera (`useSortState`), para conservarlo en la página (RF-10, RF-11).
 *
 * @template T
 * @param {{
 *   caption: string,
 *   columns: Column<T>[],
 *   rows: T[],
 *   rowKey: (row: T) => string,
 *   defaultOrder?: (a: T, b: T) => number,
 *   sortState: import('./sortCycle.js').SortState,
 *   onSortChange: (state: import('./sortCycle.js').SortState) => void,
 * }} props
 */
export function DataTable({ caption, columns, rows, rowKey, defaultOrder, sortState, onSortChange }) {
  const { t } = useTranslation()
  const { locale } = useLocale()
  const headerRefs = useRef({})
  const tbodyRef = useRef(null)
  const [stickyLeft, setStickyLeft] = useState({})

  const orderedRows = useMemo(() => {
    const byDefault = defaultOrder ? [...rows].sort(defaultOrder) : rows
    return sortRows(byDefault, columns, sortState, locale)
  }, [rows, columns, sortState, locale, defaultOrder])

  // Valor de cada celda, para resaltar las que cambian con datos nuevos (RF-30).
  const cellValues = useMemo(
    () =>
      new Map(
        orderedRows.map((row) => [
          rowKey(row),
          new Map(columns.map((column) => [column.id, JSON.stringify(column.value(row) ?? null)])),
        ]),
      ),
    [orderedRows, columns, rowKey],
  )
  const motionStore = useTableMotion(tbodyRef, cellValues)

  // Cada columna fija se coloca justo después de las fijas anteriores.
  useLayoutEffect(() => {
    const measure = () => {
      let left = 0
      const next = {}
      for (const column of columns) {
        if (!column.sticky) continue
        next[column.id] = left
        left += headerRefs.current[column.id]?.offsetWidth ?? 0
      }
      setStickyLeft((current) =>
        Object.keys(next).every((id) => current[id] === next[id]) &&
        Object.keys(current).length === Object.keys(next).length
          ? current
          : next,
      )
    }
    measure()
    if (typeof ResizeObserver === 'undefined') return undefined
    const observer = new ResizeObserver(measure)
    for (const node of Object.values(headerRefs.current)) if (node) observer.observe(node)
    return () => observer.disconnect()
  }, [columns, locale])

  const cellClass = (column, extra = '') =>
    [
      // El borde va en cada celda: así las columnas fijas lo llevan consigo al desplazar.
      'border-b border-border px-3 py-2 whitespace-nowrap',
      column.align === 'end' ? 'text-right' : 'text-left',
      column.sticky ? STICKY : '',
      extra,
    ].join(' ')
  const stickyStyle = (column) => (column.sticky ? { left: stickyLeft[column.id] ?? 0 } : undefined)

  return (
    <div className="relative overflow-x-auto rounded-md border border-border bg-surface">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => {
              const active = sortState?.columnId === column.id && column.sortKind ? sortState.direction : null
              return (
                <th
                  key={column.id}
                  ref={(node) => {
                    headerRefs.current[column.id] = node
                  }}
                  scope="col"
                  aria-sort={active ? ariaSort(column.sortKind, active) : undefined}
                  className={cellClass(column, 'font-semibold text-muted')}
                  style={stickyStyle(column)}
                >
                  {column.sortKind ? (
                    <button
                      type="button"
                      title={t('tables.sort.action', { column: column.header })}
                      onClick={() => onSortChange(nextSortState(sortState, column.id))}
                      className={`inline-flex min-h-11 items-center gap-1 rounded-md px-1 hover:bg-raised hover:text-text active:bg-border active:text-text ${
                        active ? 'text-text' : ''
                      } ${column.align === 'end' ? 'flex-row-reverse' : ''}`}
                    >
                      <span>{column.header}</span>
                      {active && <span className="sr-only">, {t(`tables.sort.${active}`)}</span>}
                      <span aria-hidden="true" className={active ? 'text-accent' : 'text-muted opacity-60'}>
                        {active ? (ariaSort(column.sortKind, active) === 'ascending' ? '▲' : '▼') : '↕'}
                      </span>
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody ref={tbodyRef} className="[&>tr:last-child>*]:border-b-0">
          {orderedRows.map((row) => (
            <RowMotionContext.Provider key={rowKey(row)} value={{ store: motionStore, rowKey: rowKey(row) }}>
              <tr data-row-key={rowKey(row)}>
                {columns.map((column) =>
                  column.rowHeader ? (
                    <th key={column.id} data-column-id={column.id} scope="row" className={cellClass(column, 'font-normal')} style={stickyStyle(column)}>
                      {column.render(row)}
                    </th>
                  ) : (
                    <td key={column.id} data-column-id={column.id} className={cellClass(column, 'tabular-nums')} style={stickyStyle(column)}>
                      {column.render(row)}
                    </td>
                  ),
                )}
              </tr>
            </RowMotionContext.Provider>
          ))}
        </tbody>
      </table>
    </div>
  )
}
