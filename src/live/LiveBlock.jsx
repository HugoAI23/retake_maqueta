import { BlockError } from '../blocks/BlockError.jsx'
import { BlockSkeleton } from '../blocks/BlockSkeleton.jsx'
import { useLiveBlock } from './useLiveBlock.js'

/**
 * Bloque de la 001 que se actualiza solo (spec 003: RF-79 a RF-88). Igual que `AsyncBlock` en la
 * primera carga; después, las recargas son silenciosas.
 *
 * @template T
 * @param {{
 *   blockName: string,
 *   load: () => Promise<T>,
 *   datasets: string[],
 *   cycle?: 'live' | 'rest',
 *   renderContent: (data: T) => import('react').ReactNode,
 *   skeletonShape?: 'generic' | 'strip',
 * }} props
 */
export function LiveBlock({ blockName, load, datasets, cycle, renderContent, skeletonShape }) {
  const { state, retry } = useLiveBlock(load, { datasets, cycle })
  if (state.status === 'loading') return <BlockSkeleton shape={skeletonShape} />
  if (state.status === 'error') return <BlockError blockName={blockName} onRetry={retry} />
  return renderContent(state.data)
}
