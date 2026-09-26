import { useCallback, useEffect, useState } from 'react'

/**
 * Orden elegido en las tablas de una página (spec 004, RF-10, RF-11, RF-11a, RF-51a; plan §2.4, D-3).
 *
 * Se guarda en la entrada del historial del navegador (`history.state`), junto con una
 * marca de la carga de la aplicación:
 * - con Atrás o Adelante, la entrada y la marca coinciden y se recupera el orden (RF-11);
 * - al entrar desde el menú o un enlace hay una entrada nueva, sin orden (RF-11a);
 * - al recargar, la entrada conserva su estado pero la marca es otra: orden por defecto (RF-11a).
 *
 * En el historial solo va el identificador de la columna, el sentido y la marca (plan §9).
 */

const HISTORY_KEY = 'retakeSort'

/** Marca de esta carga de la aplicación: cambia al recargar la página. */
const LOAD_TOKEN =
  typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2)

/** @returns {Record<string, import('./sortCycle.js').SortState>} Órdenes guardados en esta entrada y esta carga. */
function savedTables() {
  const saved = window.history.state?.[HISTORY_KEY]
  return saved?.token === LOAD_TOKEN && saved.tables ? saved.tables : {}
}

/**
 * @param {string} tableId Tabla dentro de la página.
 * @param {import('./sortCycle.js').SortState} state
 */
function saveTable(tableId, state) {
  const current = window.history.state
  const next = {
    ...(current && typeof current === 'object' ? current : {}),
    [HISTORY_KEY]: { token: LOAD_TOKEN, tables: { ...savedTables(), [tableId]: state } },
  }
  window.history.replaceState(next, '')
}

/**
 * @param {string} tableId Identificador de la tabla dentro de la página.
 * @param {unknown} [resetKey] Valor cuyo cambio vuelve al orden por defecto (p. ej. el año de la
 *   temporada: RF-51a). Cambiar de idioma o de ancho no lo toca (RF-10).
 * @returns {[import('./sortCycle.js').SortState, (state: import('./sortCycle.js').SortState) => void]}
 */
export function useSortState(tableId, resetKey) {
  const [sortState, setSortState] = useState(() => savedTables()[tableId] ?? null)
  const [lastResetKey, setLastResetKey] = useState(resetKey)
  const [pendingReset, setPendingReset] = useState(false)

  // Cambio de la clave de reinicio: vuelve al orden por defecto en este mismo pintado.
  if (!Object.is(resetKey, lastResetKey)) {
    setLastResetKey(resetKey)
    setSortState(null)
    setPendingReset(true)
  }

  useEffect(() => {
    if (!pendingReset) return
    saveTable(tableId, null)
    setPendingReset(false)
  }, [pendingReset, tableId])

  const update = useCallback(
    (state) => {
      setSortState(state)
      saveTable(tableId, state)
    },
    [tableId],
  )

  return [sortState, update]
}
