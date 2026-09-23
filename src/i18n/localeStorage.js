import { isSupportedLocale } from './locales.js'

/** Clave del almacenamiento local donde se guarda la elección del usuario (RF-66). */
export const LOCALE_STORAGE_KEY = 'retake.locale'

/**
 * Lee el idioma elegido anteriormente.
 *
 * Devuelve `null` ("sin elección") si no hay valor, si el valor fue
 * manipulado y no es `es` ni `en`, o si el almacenamiento no está
 * disponible (por ejemplo, en navegación privada). Nunca lanza errores (RF-69).
 *
 * @param {Storage | undefined} [storage]
 * @returns {import('./locales.js').LocaleCode | null}
 */
export function readStoredLocale(storage = globalThis.localStorage) {
  try {
    const value = storage?.getItem(LOCALE_STORAGE_KEY)
    return isSupportedLocale(value) ? value : null
  } catch {
    return null
  }
}

/**
 * Guarda la elección del usuario sin fecha de caducidad (RF-65, RF-66).
 * Si el almacenamiento no está disponible, la elección solo dura en la pestaña.
 *
 * @param {import('./locales.js').LocaleCode} locale
 * @param {Storage | undefined} [storage]
 */
export function saveLocale(locale, storage = globalThis.localStorage) {
  try {
    storage?.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    // Almacenamiento inaccesible: no se puede recordar, pero no se interrumpe nada.
  }
}
