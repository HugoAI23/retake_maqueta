/**
 * Etiquetas comunes de la liga (spec 002, §2.9: RF-125 y RF-126).
 *
 * Las siglas del esport se muestran igual en todos los idiomas; el resto de etiquetas
 * pasa por los diccionarios de la spec 001 (`league.*`).
 */

/** Siglas que nunca se traducen (RF-125). */
export const ACRONYMS = Object.freeze({ DQ: 'DQ', SMG: 'SMG', AR: 'AR' })

/**
 * Etiqueta traducida de la liga (RF-126).
 * @param {import('i18next').TFunction} t Función de traducción del idioma activo.
 * @param {string} key Clave dentro de `league` (p. ej. `notAvailable`).
 * @param {object} [options] Valores para interpolar.
 */
export function leagueText(t, key, options) {
  return t(`league.${key}`, options)
}

/**
 * El valor como texto, o `No disponible` si falta (nunca un espacio en blanco).
 * @param {unknown} value
 * @param {import('i18next').TFunction} t
 */
export function orNotAvailable(value, t) {
  return value === null || value === undefined || value === '' ? leagueText(t, 'notAvailable') : String(value)
}
