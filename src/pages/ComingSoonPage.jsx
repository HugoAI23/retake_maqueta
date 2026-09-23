import { useTranslation } from 'react-i18next'
import { usePageTitle } from '../shared/usePageTitle.js'

/**
 * Página de una sección cuya spec de contenido aún no está implementada (RF-37).
 *
 * @param {{ sectionId: string }} props
 */
export function ComingSoonPage({ sectionId }) {
  const { t } = useTranslation()
  const name = t(`sections.${sectionId}`)
  usePageTitle(name)

  return (
    <section className="mx-auto flex max-w-2xl flex-col items-center gap-3 py-16 text-center">
      <h1 className="text-3xl font-bold">{name}</h1>
      <p className="rounded-full bg-raised px-4 py-1 text-sm font-semibold text-muted">{t('status.comingSoon')}</p>
    </section>
  )
}
