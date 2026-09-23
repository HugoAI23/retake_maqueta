import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useTranslation } from 'react-i18next'
import { sectionsRegistry } from '../config/sectionsRegistry.js'
import { LanguageSwitcher } from '../i18n/LanguageSwitcher.jsx'
import { AnimatedButton } from '../motion/AnimatedButton.jsx'
import { useSlideAnimation } from '../motion/useSlideAnimation.js'
import { useFocusContainment } from '../shared/useFocusContainment.js'
import { MOBILE_PANEL_ID } from './CompactNavBar.jsx'
import { NavItem } from './NavItem.jsx'

/**
 * Panel del menú plegado (RF-18 a RF-22, RF-82 a RF-84).
 *
 * Contiene las ocho entradas en orden y, al final, el selector de idioma
 * (RF-19). Se pinta en un portal fuera de #root para que el resto de la
 * página pueda volverse inerte mientras está abierto (plan D-10).
 *
 * @param {{
 *   isOpen: boolean,
 *   onClose: () => void,
 *   returnFocusRef: import('react').RefObject<HTMLElement | null>,
 *   activeSectionId: string | null,
 * }} props
 */
export function MobileNavPanel({ isOpen, onClose, returnFocusRef, activeSectionId }) {
  const { t } = useTranslation()
  const panelRef = useRef(null)
  const { isRendered } = useSlideAnimation(isOpen, panelRef)

  useFocusContainment(isOpen, panelRef, returnFocusRef)

  // La página de detrás no se desplaza mientras el panel está abierto (RF-22).
  useEffect(() => {
    if (!isOpen) return undefined
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previous
    }
  }, [isOpen])

  if (!isRendered) return null

  return createPortal(
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Pulsar fuera del panel lo cierra (RF-21). */}
      <div data-testid="nav-backdrop" aria-hidden="true" onClick={onClose} className="absolute inset-0 bg-bg/80" />
      <div
        ref={panelRef}
        id={MOBILE_PANEL_ID}
        role="dialog"
        aria-modal="true"
        aria-label={t('nav.panelLabel')}
        className="absolute inset-y-0 right-0 flex w-[min(20rem,85vw)] flex-col gap-4 overflow-y-auto border-l border-border bg-surface p-4"
      >
        <div className="flex justify-end">
          <AnimatedButton
            type="button"
            onClick={onClose}
            aria-label={t('nav.closeMenu')}
            className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-md text-text hover:bg-raised active:bg-border"
          >
            <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M6 6l12 12M18 6 6 18" />
            </svg>
          </AnimatedButton>
        </div>
        <nav aria-label={t('nav.mainLabel')}>
          <ul className="flex flex-col gap-1">
            {sectionsRegistry.map((section) => (
              <li key={section.id}>
                <NavItem
                  section={section}
                  isActive={section.id === activeSectionId}
                  variant="panel"
                  onNavigate={onClose}
                />
              </li>
            ))}
          </ul>
        </nav>
        <LanguageSwitcher className="mt-auto border-t border-border pt-4" />
      </div>
    </div>,
    document.body,
  )
}
