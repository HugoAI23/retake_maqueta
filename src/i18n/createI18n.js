import i18next from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './dictionaries/en.js'
import es from './dictionaries/es.js'
import { DEFAULT_LOCALE, SUPPORTED_LOCALES } from './locales.js'

/**
 * Crea una instancia de i18next para una pestaña (decisión P-3).
 *
 * No se usa el detector de idioma de i18next: el idioma inicial lo decide
 * getInitialLocale() y se pasa aquí (RF-60 a RF-69). Tampoco se escuchan
 * cambios de otras pestañas, así cada una conserva su idioma (RF-68).
 *
 * @param {import('./locales.js').LocaleCode} locale
 */
export function createI18n(locale) {
  const instance = i18next.createInstance()
  instance.use(initReactI18next).init({
    resources: { es: { translation: es }, en: { translation: en } },
    lng: locale,
    fallbackLng: DEFAULT_LOCALE,
    supportedLngs: SUPPORTED_LOCALES,
    // React ya escapa todo el texto que pinta (constitución §6).
    interpolation: { escapeValue: false },
    initAsync: false,
  })
  return instance
}
