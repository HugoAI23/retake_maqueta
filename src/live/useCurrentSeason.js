import { useEffect, useState } from 'react'
import { getCurrentSeason } from '../league/leagueApi.js'
import { useLive } from './LiveProvider.jsx'

/** El pie cambia de año en 5 min como máximo cuando cambia la temporada (RF-77). */
export const SEASON_REFRESH_MS = 300_000

/**
 * Año de la temporada actual para el pie (spec 003: RF-74 a RF-78). Sustituye al valor
 * provisional de `src/config/season.js` de la 001.
 *
 * - Sin año hasta obtenerlo (RF-76).
 * - Si una consulta posterior falla, mantiene el año ya mostrado (RF-78, Q-47).
 * - Se vuelve a pedir cada 5 min y cuando el canal avisa de un cambio de temporada.
 *
 * @returns {number | null}
 */
export function useCurrentSeason() {
  const { subscribe } = useLive()
  const [year, setYear] = useState(null)

  useEffect(() => {
    let active = true
    const refresh = () =>
      getCurrentSeason()
        .then((season) => active && season && setYear(season.year))
        .catch(() => {}) // se mantiene el año ya mostrado (RF-78)
    refresh()
    const interval = setInterval(refresh, SEASON_REFRESH_MS)
    const unsubscribe = subscribe((event) => {
      if (event.type === 'change' && event.datasets.includes('season')) refresh()
    })
    return () => {
      active = false
      clearInterval(interval)
      unsubscribe()
    }
  }, [subscribe])

  return year
}
