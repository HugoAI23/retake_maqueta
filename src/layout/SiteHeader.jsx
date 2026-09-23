import { useRef } from 'react'
import { LanguageSwitcher } from '../i18n/LanguageSwitcher.jsx'
import { useActiveSection } from '../navigation/useActiveSection.js'
import { useNavPanelState } from '../navigation/useNavPanelState.js'
import { Logo } from '../shared/Logo.jsx'
import { CompactNavBar } from './CompactNavBar.jsx'
import { MainNav } from './MainNav.jsx'
import { MobileNavPanel } from './MobileNavPanel.jsx'

/**
 * Cabecera con el menú de navegación (plan §1.3).
 *
 * - Desde 1024 px: logo, ocho entradas y selector de idioma en una fila (RF-7).
 * - Por debajo: logo, acceso a Modelos de ML y botón de menú (RF-16, RF-17).
 * Ninguna de las dos queda fija al hacer scroll (RF-3).
 */
export function SiteHeader() {
  const activeSectionId = useActiveSection()
  const panel = useNavPanelState()
  const menuButtonRef = useRef(null)

  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-2 px-4 py-2">
        <Logo />
        <MainNav activeSectionId={activeSectionId} />
        <LanguageSwitcher className="hidden lg:flex" />
        <CompactNavBar
          isOpen={panel.isOpen}
          onToggle={panel.toggle}
          buttonRef={menuButtonRef}
          activeSectionId={activeSectionId}
        />
      </div>
      <MobileNavPanel
        isOpen={panel.isOpen}
        onClose={panel.close}
        returnFocusRef={menuButtonRef}
        activeSectionId={activeSectionId}
      />
    </header>
  )
}
