/**
 * Formato de las cifras de las tablas de datos (spec 004, RF-20 a RF-23).
 *
 * Los dígitos siguen el formato del idioma de la interfaz (RF-23). El signo de las
 * diferencias es siempre `+` o `−` (U+2212), en cualquier idioma (RF-21).
 */

const MINUS = '−'
const EN_DASH = '–'

/**
 * @param {number} value
 * @param {import('../i18n/locales.js').LocaleCode} locale
 * @returns {string} Cifra con los separadores del idioma, sin signo propio del idioma.
 */
export function formatNumber(value, locale) {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(value)
}

/**
 * Balance "ganados–perdidos" con una raya entre las dos cifras (RF-20), p. ej. `12–5`.
 * @param {{ won: number, lost: number }} record
 * @param {import('../i18n/locales.js').LocaleCode} locale
 */
export function formatRecord(record, locale) {
  return `${formatNumber(record.won, locale)}${EN_DASH}${formatNumber(record.lost, locale)}`
}

/**
 * Diferencia con su signo (RF-21): `+8`, `−3` o `0`.
 * @param {number} value
 * @param {import('../i18n/locales.js').LocaleCode} locale
 */
export function formatDiff(value, locale) {
  if (value === 0) return formatNumber(0, locale)
  return `${value > 0 ? '+' : MINUS}${formatNumber(Math.abs(value), locale)}`
}

/**
 * Tono de color de una diferencia (RF-22): el color distingue además del signo.
 * @param {number} value
 * @returns {'positive' | 'negative' | 'neutral'}
 */
export function diffTone(value) {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}
