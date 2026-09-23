import { useTranslation } from 'react-i18next'
import { AnimatedButton } from '../motion/AnimatedButton.jsx'
import { useLocale } from './LocaleProvider.jsx'

// Cada opción se nombra en su propio idioma para que se reconozca aunque la
// interfaz esté en el otro (RF-59, RF-79). Son nombres fijos, no se traducen.
const OPTIONS = [
  { code: 'es', short: 'ES', name: 'Español' },
  { code: 'en', short: 'EN', name: 'English' },
]

/**
 * Selector de idioma de dos botones (plan D-14). El activo se anuncia como
 * pulsado. Cambiar de idioma no saca al usuario de la página (RF-63, RF-64).
 *
 * @param {{ className?: string }} props
 */
export function LanguageSwitcher({ className = '' }) {
  const { t } = useTranslation()
  const { locale, changeLocale } = useLocale()

  return (
    <div role="group" aria-label={t('language.label')} className={`flex items-center gap-1 ${className}`}>
      {OPTIONS.map((option) => {
        const active = option.code === locale
        return (
          <AnimatedButton
            key={option.code}
            type="button"
            lang={option.code}
            aria-label={option.name}
            aria-pressed={active}
            onClick={() => {
              if (!active) changeLocale(option.code)
            }}
            className={`min-h-11 min-w-11 rounded-md px-2 text-sm font-semibold transition-colors ${
              active
                ? 'bg-text text-bg hover:bg-muted active:bg-border active:text-text'
                : 'text-muted hover:bg-raised hover:text-text active:bg-border'
            }`}
          >
            {option.short}
          </AnimatedButton>
        )
      })}
    </div>
  )
}
