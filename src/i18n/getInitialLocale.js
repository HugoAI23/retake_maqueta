import { readStoredLocale } from './localeStorage.js'
import { resolveInitialLocale } from './resolveInitialLocale.js'

/**
 * Idioma con el que arranca una pestaña.
 *
 * La elección guardada en Retake manda sobre el idioma del navegador (RF-65,
 * RF-67). Si no hay elección válida, se aplica la regla de primera visita
 * (RF-69). Se llama una sola vez al cargar la pestaña (RF-68).
 *
 * @param {{ storage?: Storage, browserLanguages?: readonly string[] }} [sources]
 * @returns {import('./locales.js').LocaleCode}
 */
export function getInitialLocale({
  storage = globalThis.localStorage,
  browserLanguages = globalThis.navigator?.languages,
} = {}) {
  return readStoredLocale(storage) ?? resolveInitialLocale(browserLanguages)
}
