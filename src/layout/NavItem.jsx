import { useTranslation } from 'react-i18next'
import { Link } from 'react-router'
import { useScrollTopOnSameSection } from '../navigation/useScrollTopOnSameSection.js'
import { MlIcon } from './MlIcon.jsx'

const VARIANT_CLASSES = {
  row: 'min-h-11 px-2.5 text-sm',
  panel: 'min-h-12 w-full px-3 text-base',
  compact: 'min-h-11 px-2.5 text-sm',
}

/**
 * Una entrada del menú (plan §2.1).
 *
 * - Activa: subrayada e indicada como página actual a los lectores de pantalla (RF-24, RF-80).
 * - Destacada (Modelos de ML): fondo exclusivo, icono y etiqueta "IA" (RF-8 a RF-10).
 * - Pulsar la sección actual lleva al principio de la página (RF-15).
 *
 * @param {{
 *   section: import('../config/sectionsRegistry.js').SectionDefinition,
 *   isActive: boolean,
 *   variant?: 'row' | 'panel' | 'compact',
 *   onNavigate?: () => void,
 * }} props
 */
export function NavItem({ section, isActive, variant = 'row', onNavigate }) {
  const { t } = useTranslation()
  const scrollTopIfSameSection = useScrollTopOnSameSection()

  const tone = section.featured
    ? 'bg-ml text-on-ml hover:ring-2 hover:ring-on-ml active:translate-y-px'
    : 'text-muted hover:bg-raised hover:text-text active:bg-border active:text-text'
  const active = isActive
    ? `underline decoration-2 underline-offset-8 ${section.featured ? 'decoration-on-ml' : 'text-text decoration-accent'}`
    : ''

  return (
    <Link
      to={section.path}
      aria-current={isActive ? 'page' : undefined}
      data-featured={section.featured || undefined}
      onClick={(event) => {
        scrollTopIfSameSection(event, section.path)
        onNavigate?.()
      }}
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-md font-semibold transition-colors ${VARIANT_CLASSES[variant]} ${tone} ${active}`}
    >
      {section.featured && <MlIcon />}
      <span>{t(`sections.${section.id}`)}</span>
      {section.featured && (
        <span className="rounded bg-on-ml px-1 text-xs font-black text-ml no-underline">{t('nav.mlBadge')}</span>
      )}
    </Link>
  )
}
