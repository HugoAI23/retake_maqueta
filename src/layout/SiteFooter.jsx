import { useTranslation } from 'react-i18next'
import { currentSeason } from '../config/season.js'

/**
 * Pie de página: nombre, aviso de proyecto escolar y año de la temporada
 * actual (RF-56 a RF-58).
 *
 * @param {{ season?: import('../config/season.js').SeasonInfo }} props
 */
export function SiteFooter({ season = currentSeason }) {
  const { t } = useTranslation()

  return (
    <footer className="mt-auto border-t border-border bg-surface">
      <div className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-6 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
        <p className="font-bold text-text">Retake</p>
        <p>{t('footer.disclaimer')}</p>
        <p>{t('footer.season', { year: season.year })}</p>
      </div>
    </footer>
  )
}
