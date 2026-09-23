import { useTranslation } from 'react-i18next'
import { AsyncBlock } from './AsyncBlock.jsx'
import { ComingSoonBlock } from './ComingSoonBlock.jsx'

/**
 * Punto de entrada de cada hueco de bloque (plan §1.6).
 *
 * Sin contenido: muestra "Próximamente" y NO pone en marcha ninguna carga
 * (RF-38, RF-39). Con contenido: delega en AsyncBlock.
 *
 * @param {{
 *   block: import('../config/homeBlocksRegistry.js').HomeBlockDefinition,
 *   load?: () => Promise<unknown>,
 *   renderContent?: (data: unknown) => import('react').ReactNode,
 *   skeletonShape?: 'generic' | 'strip',
 *   compact?: boolean,
 * }} props
 */
export function BlockSlot({ block, load, renderContent, skeletonShape, compact = false }) {
  const { t } = useTranslation()

  if (!block.hasContent) return <ComingSoonBlock blockId={block.id} compact={compact} />

  return (
    <AsyncBlock
      blockName={t(`blocks.${block.id}`)}
      load={load}
      renderContent={renderContent}
      skeletonShape={skeletonShape}
    />
  )
}
