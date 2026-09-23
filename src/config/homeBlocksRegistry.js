/**
 * Registro de los bloques con contenido de la liga (plan §3.2).
 *
 * En la spec 001 ningún bloque tiene contenido: todos muestran su nombre y
 * "Próximamente" sin intentar cargar nada (RF-38, RF-39). Cada spec de
 * contenido cambiará `hasContent` de su bloque.
 *
 * @typedef {object} HomeBlockDefinition
 * @property {'ticker' | 'spotlight' | 'news' | 'matchGrid'} id Identificador; también es la clave del nombre en `blocks.<id>`.
 * @property {boolean} hasContent Si su spec de contenido está implementada.
 */

/** @type {Readonly<Record<HomeBlockDefinition['id'], HomeBlockDefinition>>} */
export const homeBlocksRegistry = Object.freeze({
  ticker: { id: 'ticker', hasContent: false },
  spotlight: { id: 'spotlight', hasContent: false },
  news: { id: 'news', hasContent: false },
  matchGrid: { id: 'matchGrid', hasContent: false },
})
