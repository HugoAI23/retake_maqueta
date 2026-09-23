import { BrowserRouter } from 'react-router'
import { ConnectionProvider } from '../connection/ConnectionProvider.jsx'
import { LocaleProvider } from '../i18n/LocaleProvider.jsx'
import { MotionProvider } from '../motion/MotionProvider.jsx'
import { AppRoutes } from './AppRoutes.jsx'

/**
 * Raíz de la aplicación: proveedores globales (movimiento, idioma, conexión)
 * y enrutador (plan §1.1).
 */
export function App() {
  return (
    <MotionProvider>
      <LocaleProvider>
        <ConnectionProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </ConnectionProvider>
      </LocaleProvider>
    </MotionProvider>
  )
}
