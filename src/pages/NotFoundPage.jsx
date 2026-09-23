import { useTranslation } from 'react-i18next'
import { Link } from 'react-router'
import { usePageTitle } from '../shared/usePageTitle.js'

/**
 * Página para direcciones que no existen en Retake (RF-54, RF-55).
 * No muestra la dirección escrita por el usuario (plan §5, XSS).
 */
export function NotFoundPage() {
  const { t } = useTranslation()
  usePageTitle(t('notFound.title'))

  return (
    <section className="mx-auto flex max-w-2xl flex-col items-center gap-4 py-16 text-center">
      <h1 className="text-3xl font-bold">{t('notFound.title')}</h1>
      <p className="text-muted">{t('notFound.message')}</p>
      <Link
        to="/"
        className="inline-flex min-h-11 items-center rounded-md bg-accent px-4 font-semibold text-bg hover:bg-text active:bg-muted"
      >
        {t('notFound.backHome')}
      </Link>
    </section>
  )
}
