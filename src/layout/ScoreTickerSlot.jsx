import { useTranslation } from 'react-i18next'
import { BlockSlot } from '../blocks/BlockSlot.jsx'
import { homeBlocksRegistry } from '../config/homeBlocksRegistry.js'

/**
 * Franja de la cinta de marcadores: todo el ancho, encima del menú (RF-2).
 * Su contenido lo definirá su propia spec; mientras tanto, "Próximamente" (RF-38).
 */
export function ScoreTickerSlot() {
  const { t } = useTranslation()

  return (
    <section aria-label={t('blocks.ticker')} data-testid="score-ticker" className="w-full border-b border-border bg-bg">
      <div className="mx-auto max-w-7xl px-4 py-2">
        <BlockSlot block={homeBlocksRegistry.ticker} skeletonShape="strip" compact />
      </div>
    </section>
  )
}
