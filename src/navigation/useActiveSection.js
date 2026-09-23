import { matchRoutes, useLocation } from 'react-router'
import { routeDefinitions } from '../app/routeDefinitions.js'

/**
 * Sección activa de una dirección (RF-24, RF-25).
 *
 * Se calcula a partir de la RUTA QUE HA COINCIDIDO, no del texto de la
 * dirección: una subpágina definida activa su sección madre, pero una
 * dirección sin ruta (p. ej. `/players/xyz` mientras no exista esa subpágina)
 * cae en "Página no encontrada" y no activa ninguna.
 *
 * @param {string} pathname
 * @param {import('../app/routeDefinitions.js').RouteDefinition[]} definitions
 * @returns {string | null} Identificador de la sección o `null`.
 */
export function resolveActiveSectionId(pathname, definitions) {
  const matches = matchRoutes(definitions, pathname) ?? []
  for (let i = matches.length - 1; i >= 0; i -= 1) {
    const { sectionId } = matches[i].route
    if (sectionId) return sectionId
  }
  return null
}

/** @returns {string | null} Sección activa de la dirección actual. */
export function useActiveSection() {
  const { pathname } = useLocation()
  return resolveActiveSectionId(pathname, routeDefinitions)
}
