import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { getFreshness } from '../league/leagueApi.js'
import { isStale, STALE_THRESHOLD_MS } from './freshnessRules.js'
import { createLiveChannel } from './liveChannel.js'

const LiveContext = createContext(null)
const INERT = { subscribe: () => () => {}, cutSince: null, freshness: {} }

/**
 * Comparte el canal de eventos de la pestaña y la frescura de cada conjunto de datos
 * (spec 003: RF-79 a RF-82, RF-89, RF-155; plan §2.6).
 *
 * La frescura se pide a `/api/freshness` al abrir la página, tras cada cambio y al volver a
 * la pestaña; los avisos `freshness` del canal la corrigen al momento.
 *
 * @param {{ children: import('react').ReactNode, channel?: ReturnType<typeof createLiveChannel>,
 *   loadFreshness?: () => Promise<Record<string, { lastChangedAt: string | null, stale: boolean }>> }} props
 */
export function LiveProvider({ children, channel: given, loadFreshness = getFreshness }) {
  const [channel] = useState(() => given ?? createLiveChannel())
  const [cutSince, setCutSince] = useState(null)
  const [freshness, setFreshness] = useState({})

  useEffect(() => {
    let active = true
    const refresh = () =>
      loadFreshness()
        .then((data) => active && data && setFreshness(data))
        .catch(() => {}) // sin frescura se sigue mostrando lo que haya (RF-91)
    refresh()
    const unsubscribe = channel.subscribe((event) => {
      if (event.type === 'status') setCutSince(event.cutSince)
      else if (event.type === 'freshness')
        setFreshness((current) => {
          const next = { ...current }
          for (const [dataset, stale] of Object.entries(event.stale)) next[dataset] = { ...next[dataset], stale }
          return next
        })
      else if (event.type === 'change' || event.type === 'visible') refresh()
    })
    return () => {
      active = false
      unsubscribe()
    }
  }, [channel, loadFreshness])

  useEffect(() => () => channel.close(), [channel])

  const value = useMemo(() => ({ subscribe: channel.subscribe, cutSince, freshness }), [channel, cutSince, freshness])
  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>
}

/** Canal y frescura; fuera de `LiveProvider`, un canal inerte (páginas sin datos en vivo, pruebas). */
export function useLive() {
  return useContext(LiveContext) ?? INERT
}

/**
 * Frescura de un conjunto para un bloque: último cambio y si está sin actualizar (RF-89, RF-158).
 * @param {string} dataset
 */
export function useDatasetFreshness(dataset) {
  const { cutSince, freshness } = useLive()
  const [, repaint] = useState(0)
  const entry = freshness[dataset] ?? {}
  // Con el canal cortado, el aviso aparece al pasar el umbral aunque no llegue ningún evento.
  useEffect(() => {
    if (cutSince == null) return undefined
    const threshold = dataset === 'live' ? STALE_THRESHOLD_MS.live : STALE_THRESHOLD_MS.rest
    const timer = setTimeout(() => repaint((n) => n + 1), Math.max(0, cutSince + threshold - Date.now()) + 1)
    return () => clearTimeout(timer)
  }, [cutSince, dataset])
  return {
    lastChangedAt: entry.lastChangedAt ?? null,
    stale: isStale({ dataset, serverStale: Boolean(entry.stale), cutSince, now: Date.now() }),
  }
}
