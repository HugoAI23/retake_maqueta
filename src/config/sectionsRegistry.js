/**
 * Registro de las secciones del menú (plan §3.1, decisión D-3).
 *
 * El orden del array es el orden del menú (RF-6). Cada sección tiene su
 * dirección propia (RF-26). `hasContent` pasa a `true` cuando se implementa la
 * spec de contenido de la sección; mientras sea `false` muestra "Próximamente"
 * (RF-37).
 *
 * @typedef {object} SectionDefinition
 * @property {string} id Identificador interno; también es la clave del nombre en `sections.<id>`.
 * @property {string} path Dirección propia de la sección.
 * @property {boolean} featured `true` solo para Modelos de ML (RF-8 a RF-10, RF-17).
 * @property {boolean} hasContent Si su spec de contenido está implementada.
 */

/** @type {readonly SectionDefinition[]} */
export const sectionsRegistry = Object.freeze([
  { id: 'home', path: '/', featured: false, hasContent: true },
  { id: 'matches', path: '/matches', featured: false, hasContent: false },
  { id: 'teams', path: '/teams', featured: false, hasContent: false },
  { id: 'players', path: '/players', featured: false, hasContent: false },
  { id: 'tournaments', path: '/tournaments', featured: false, hasContent: false },
  { id: 'standings', path: '/standings', featured: false, hasContent: true },
  { id: 'news', path: '/news', featured: false, hasContent: false },
  { id: 'mlModels', path: '/ml-models', featured: true, hasContent: false },
])

/** Sección destacada (Modelos de ML). */
export const featuredSection = sectionsRegistry.find((section) => section.featured)

/**
 * @param {string} id
 * @returns {SectionDefinition | undefined}
 */
export function getSection(id) {
  return sectionsRegistry.find((section) => section.id === id)
}
