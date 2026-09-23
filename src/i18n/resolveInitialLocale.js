import { DEFAULT_LOCALE, isSupportedLocale } from './locales.js'

/**
 * Regla de primera visita (RF-60 a RF-62).
 *
 * Recorre la lista de idiomas preferidos del navegador en orden, reduce cada
 * variante regional a su idioma base (`es-MX` → `es`, `en-GB` → `en`) y
 * devuelve el primero admitido. Si ninguno lo es, devuelve español.
 *
 * @param {readonly string[] | undefined} browserLanguages Normalmente `navigator.languages`.
 * @returns {import('./locales.js').LocaleCode}
 */
export function resolveInitialLocale(browserLanguages) {
  for (const tag of browserLanguages ?? []) {
    const base = String(tag).toLowerCase().split('-')[0]
    if (isSupportedLocale(base)) return base
  }
  return DEFAULT_LOCALE
}
