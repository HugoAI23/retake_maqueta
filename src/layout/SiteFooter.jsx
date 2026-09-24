import { useTranslation } from 'react-i18next'
import { useCurrentSeason } from '../live/useCurrentSeason.js'

/** Fuentes de los datos, con un enlace a cada una (spec 003, RF-160; cambio C-11 de la 001). */
export const SOURCES = [
  { name: 'BreakingPoint.gg', href: 'https://www.breakingpoint.gg' },
  { name: 'Call of Duty Esports Wiki', href: 'https://cod-esports.fandom.com' },
  { name: 'Call of Duty League', href: 'https://www.callofdutyleague.com' },
]
const WIKI_LICENSE = 'https://creativecommons.org/licenses/by-sa/3.0/'

/**
 * Pie de página: nombre, aviso de proyecto escolar, año de la temporada actual (RF-56 a RF-58 de
 * la 001; RF-74 a RF-78 de la 003) y atribución de las fuentes (RF-160 de la 003).
 *
 * El año sale de la API: no aparece hasta obtenerlo y se mantiene si luego falla.
 */
export function SiteFooter() {
  const { t } = useTranslation()
  const year = useCurrentSeason()
  const link = 'underline decoration-1 underline-offset-2 hover:text-accent focus-visible:text-accent'

  return (
    <footer className="mt-auto border-t border-border bg-surface">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-6 text-sm text-muted">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-bold text-text">Retake</p>
          <p>{t('footer.disclaimer')}</p>
          {year != null && <p>{t('footer.season', { year })}</p>}
        </div>
        <p>
          {t('footer.dataFrom')}{' '}
          {SOURCES.map((source, index) => (
            <span key={source.href}>
              <a href={source.href} className={link} rel="noopener noreferrer">
                {source.name}
              </a>
              {index < SOURCES.length - 1 ? ', ' : '. '}
            </span>
          ))}
          <a href={WIKI_LICENSE} className={link} rel="noopener noreferrer">
            {t('footer.wikiLicense')}
          </a>
        </p>
      </div>
    </footer>
  )
}
