import { useTranslation } from 'react-i18next'
import { sectionsRegistry } from '../config/sectionsRegistry.js'
import { NavItem } from './NavItem.jsx'

/**
 * Fila horizontal con las ocho entradas del menú, visible desde 1024 px
 * (RF-6, RF-7). Por debajo se oculta solo con estilos (plan D-1, D-2).
 *
 * @param {{ activeSectionId: string | null }} props
 */
export function MainNav({ activeSectionId }) {
  const { t } = useTranslation()

  return (
    <nav aria-label={t('nav.mainLabel')} className="hidden lg:block">
      <ul className="flex items-center gap-0.5">
        {sectionsRegistry.map((section) => (
          <li key={section.id}>
            <NavItem section={section} isActive={section.id === activeSectionId} />
          </li>
        ))}
      </ul>
    </nav>
  )
}
