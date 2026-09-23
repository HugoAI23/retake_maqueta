import { AppRoutes } from '../app/AppRoutes.jsx'
import { renderWithProviders } from './renderWithProviders.jsx'

/**
 * Pinta la aplicación completa (marco + rutas) en una dirección.
 * @param {string} route
 * @param {{ locale?: 'es' | 'en', reducedMotion?: boolean }} [options]
 */
export function renderApp(route = '/', options = {}) {
  return renderWithProviders(<AppRoutes />, { ...options, route })
}
