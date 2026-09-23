import { useTranslation } from 'react-i18next'
import { BlockSlot } from '../blocks/BlockSlot.jsx'
import { homeBlocksRegistry } from '../config/homeBlocksRegistry.js'
import { usePageTitle } from '../shared/usePageTitle.js'

/**
 * Página de inicio: solo reserva los huecos de sus bloques (RF-32 a RF-36).
 *
 * - Desde 1024 px: spotlight en 2/3, noticias en 1/3 a su derecha y la
 *   cuadrícula de partidos debajo, a todo el ancho.
 * - Por debajo: una columna con spotlight, noticias y cuadrícula.
 * La distribución se hace solo con estilos, así los bloques no se desmontan
 * al cambiar de tamaño y conservan su estado (RF-49, plan D-1).
 */
export function HomePage() {
  const { t } = useTranslation()
  usePageTitle(null)

  return (
    <>
      <h1 className="sr-only">{t('home.heading')}</h1>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div data-testid="slot-spotlight" className="lg:col-span-2 lg:min-h-80">
          <BlockSlot block={homeBlocksRegistry.spotlight} />
        </div>
        <div data-testid="slot-news">
          <BlockSlot block={homeBlocksRegistry.news} />
        </div>
        <div data-testid="slot-matchGrid" className="lg:col-span-3">
          <BlockSlot block={homeBlocksRegistry.matchGrid} />
        </div>
      </div>
    </>
  )
}
