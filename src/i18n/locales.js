/**
 * Idiomas admitidos por la interfaz (RF-59).
 * @typedef {'es' | 'en'} LocaleCode
 */

/** @type {LocaleCode[]} */
export const SUPPORTED_LOCALES = ['es', 'en']

/** Idioma por defecto cuando el navegador no prefiere ninguno admitido (RF-62). */
export const DEFAULT_LOCALE = 'es'

/**
 * Indica si un valor es un idioma admitido.
 * @param {unknown} value
 * @returns {value is LocaleCode}
 */
export function isSupportedLocale(value) {
  return SUPPORTED_LOCALES.includes(value)
}
