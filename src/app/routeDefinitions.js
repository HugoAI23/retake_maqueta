import { sectionsRegistry } from '../config/sectionsRegistry.js'

/**
 * @typedef {object} RouteDefinition
 * @property {string} path
 * @property {'home' | 'content' | 'comingSoon' | 'admin' | 'demo' | 'notFound'} kind Qué página se pinta.
 * @property {string} [sectionId] Sección del menú a la que pertenece (para la entrada activa).
 */

/**
 * Genera la tabla de rutas a partir del registro de secciones (plan §1.1, D-3).
 * No contiene componentes: así la pueden usar tanto el enrutador como el
 * cálculo de la sección activa, sin dependencias circulares.
 *
 * @param {{ devRoutes?: RouteDefinition[] }} [options] Rutas que solo existen en desarrollo.
 * @returns {RouteDefinition[]}
 */
export function buildRouteDefinitions({ devRoutes = [] } = {}) {
  const sectionRoutes = sectionsRegistry.map((section) => ({
    path: section.path,
    sectionId: section.id,
    kind: section.id === 'home' ? 'home' : section.hasContent ? 'content' : 'comingSoon',
  }))

  // `/admin` (spec 003, RF-97 a RF-99): dentro del marco, sin sección ni entrada en el menú.
  return [...sectionRoutes, { path: '/admin', kind: 'admin' }, ...devRoutes, { path: '*', kind: 'notFound' }]
}

/**
 * Rutas de la aplicación en el entorno actual.
 *
 * La página de demostración (RF-89) solo se añade en desarrollo. En la versión
 * de producción `import.meta.env.DEV` vale `false`, así que su dirección ni
 * siquiera llega al paquete y responde "Página no encontrada" (RF-95).
 */
export const routeDefinitions = buildRouteDefinitions({
  devRoutes: import.meta.env.DEV ? [{ path: '/dev/block-demo', kind: 'demo' }] : [],
})
