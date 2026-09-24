import { BrowserRouter } from 'react-router'
import { ConnectionProvider } from '../connection/ConnectionProvider.jsx'
import { LocaleProvider } from '../i18n/LocaleProvider.jsx'
import { LiveAnnouncerProvider } from '../live/LiveAnnouncer.jsx'
import { LiveProvider } from '../live/LiveProvider.jsx'
import { MotionProvider } from '../motion/MotionProvider.jsx'
import { AppRoutes } from './AppRoutes.jsx'

/**
 * Raíz de la aplicación: proveedores globales (movimiento, idioma, conexión, canal de eventos
 * y anuncios en vivo de la spec 003) y enrutador (plan §1.1).
 */
export function App() {
  return (
    <MotionProvider>
      <LocaleProvider>
        <ConnectionProvider>
          <LiveProvider>
            <LiveAnnouncerProvider>
              <BrowserRouter>
                <AppRoutes />
              </BrowserRouter>
            </LiveAnnouncerProvider>
          </LiveProvider>
        </ConnectionProvider>
      </LocaleProvider>
    </MotionProvider>
  )
}
