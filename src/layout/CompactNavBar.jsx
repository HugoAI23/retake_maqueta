import { useTranslation } from 'react-i18next'
import { featuredSection } from '../config/sectionsRegistry.js'
import { AnimatedButton } from '../motion/AnimatedButton.jsx'
import { NavItem } from './NavItem.jsx'

export const MOBILE_PANEL_ID = 'mobile-nav-panel'

/**
 * Barra del menú plegado, por debajo de 1024 px (RF-16, RF-17): acceso
 * directo a Modelos de ML y botón de menú. El logo lo pone la cabecera.
 *
 * @param {{
 *   isOpen: boolean,
 *   onToggle: () => void,
 *   buttonRef: import('react').RefObject<HTMLButtonElement | null>,
 *   activeSectionId: string | null,
 * }} props
 */
export function CompactNavBar({ isOpen, onToggle, buttonRef, activeSectionId }) {
  const { t } = useTranslation()

  return (
    <div className="flex items-center gap-2 lg:hidden">
      <NavItem section={featuredSection} isActive={featuredSection.id === activeSectionId} variant="compact" />
      <AnimatedButton
        ref={buttonRef}
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-controls={MOBILE_PANEL_ID}
        aria-label={isOpen ? t('nav.closeMenu') : t('nav.openMenu')}
        className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-md text-text hover:bg-raised active:bg-border"
      >
        <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </AnimatedButton>
    </div>
  )
}
