import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { ConnectionProvider } from '../connection/ConnectionProvider.jsx'
import { LocaleProvider } from '../i18n/LocaleProvider.jsx'
import { MotionProvider } from '../motion/MotionProvider.jsx'

/**
 * Pinta un componente con los proveedores globales de la aplicación.
 * Por defecto: español, reducir movimiento activado (pruebas deterministas)
 * y dirección "/".
 *
 * @param {import('react').ReactElement} ui
 * @param {{ locale?: 'es' | 'en', route?: string, reducedMotion?: boolean }} [options]
 */
export function renderWithProviders(ui, { locale = 'es', route = '/', reducedMotion = true } = {}) {
  return render(
    <MotionProvider forceReducedMotion={reducedMotion}>
      <LocaleProvider initialLocale={locale}>
        <ConnectionProvider>
          <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
        </ConnectionProvider>
      </LocaleProvider>
    </MotionProvider>,
  )
}
