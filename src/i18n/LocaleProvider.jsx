import { createContext, useCallback, useContext, useLayoutEffect, useMemo, useState } from 'react'
import { I18nextProvider } from 'react-i18next'
import { createI18n } from './createI18n.js'
import { formatDate, formatDateTime, formatTime } from './formatters.js'
import { getInitialLocale } from './getInitialLocale.js'
import { saveLocale } from './localeStorage.js'

const LocaleContext = createContext(null)

/**
 * Proveedor del idioma de la interfaz (plan §1.8).
 *
 * Lee el idioma una sola vez al montar la pestaña (RF-68). Cambiar de idioma
 * guarda la elección (RF-65), actualiza el atributo `lang` del documento y
 * vuelve a pintar los textos sin desmontar la página (RF-63, RF-64).
 *
 * @param {{ children: import('react').ReactNode, initialLocale?: import('./locales.js').LocaleCode }} props
 *   `initialLocale` solo se usa en pruebas; en la aplicación se calcula con getInitialLocale().
 */
export function LocaleProvider({ children, initialLocale }) {
  const [locale, setLocale] = useState(() => initialLocale ?? getInitialLocale())
  const [i18n] = useState(() => createI18n(locale))

  useLayoutEffect(() => {
    document.documentElement.lang = locale
  }, [locale])

  const changeLocale = useCallback(
    (next) => {
      saveLocale(next)
      i18n.changeLanguage(next)
      setLocale(next)
    },
    [i18n],
  )

  const value = useMemo(
    () => ({
      locale,
      changeLocale,
      formatDate: (date) => formatDate(date, locale),
      formatTime: (date) => formatTime(date, locale),
      formatDateTime: (date) => formatDateTime(date, locale),
    }),
    [locale, changeLocale],
  )

  return (
    <I18nextProvider i18n={i18n}>
      <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
    </I18nextProvider>
  )
}

/**
 * Idioma activo, acción para cambiarlo y formateadores ligados al idioma.
 * @returns {{ locale: 'es' | 'en', changeLocale: (l: 'es' | 'en') => void,
 *   formatDate: (d: Date) => string, formatTime: (d: Date) => string, formatDateTime: (d: Date) => string }}
 */
export function useLocale() {
  const value = useContext(LocaleContext)
  if (!value) throw new Error('useLocale debe usarse dentro de <LocaleProvider>')
  return value
}
