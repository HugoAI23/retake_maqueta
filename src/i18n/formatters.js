/**
 * Formato de fechas y horas según el idioma activo (RF-71), con la API de
 * internacionalización nativa del navegador (Intl).
 */

/**
 * @param {Date | number} date
 * @param {import('./locales.js').LocaleCode} locale
 * @returns {string} Fecha larga, p. ej. "21 de septiembre de 2026" / "September 21, 2026".
 */
export function formatDate(date, locale) {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'long' }).format(date)
}

/**
 * @param {Date | number} date
 * @param {import('./locales.js').LocaleCode} locale
 * @returns {string} Hora corta, p. ej. "18:30" / "6:30 PM".
 */
export function formatTime(date, locale) {
  return new Intl.DateTimeFormat(locale, { timeStyle: 'short' }).format(date)
}

/**
 * @param {Date | number} date
 * @param {import('./locales.js').LocaleCode} locale
 * @returns {string} Fecha y hora juntas.
 */
export function formatDateTime(date, locale) {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'long', timeStyle: 'short' }).format(date)
}
