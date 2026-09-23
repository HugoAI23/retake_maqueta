import { useTranslation } from 'react-i18next'
import { Outlet } from 'react-router'
import { PageTransition } from '../motion/PageTransition.jsx'
import { OfflineBanner } from './OfflineBanner.jsx'
import { ScoreTickerSlot } from './ScoreTickerSlot.jsx'
import { SiteFooter } from './SiteFooter.jsx'
import { SiteHeader } from './SiteHeader.jsx'

/**
 * Marco común de todas las páginas, incluidas "Próximamente" y "Página no
 * encontrada" (RF-1): de arriba abajo, cinta de marcadores, menú, aviso de
 * conexión, zona de contenido y pie. Nada queda fijo al hacer scroll (RF-3).
 *
 * El enlace "Saltar al contenido" permite saltarse la cinta y el menú con el
 * teclado (WCAG 2.4.1, RF-73).
 */
export function AppShell() {
  const { t } = useTranslation()

  return (
    <div className="flex min-h-screen flex-col overflow-x-clip">
      <a
        href="#main-content"
        className="sr-only z-50 rounded-md bg-focus px-4 py-2 font-semibold text-bg focus:not-sr-only focus:absolute focus:top-2 focus:left-2"
      >
        {t('app.skipToContent')}
      </a>
      <ScoreTickerSlot />
      <SiteHeader />
      <OfflineBanner />
      <main id="main-content" tabIndex={-1} className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 outline-none">
        <PageTransition>
          <Outlet />
        </PageTransition>
      </main>
      <SiteFooter />
    </div>
  )
}
