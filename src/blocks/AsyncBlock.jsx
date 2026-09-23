import { BlockError } from './BlockError.jsx'
import { BlockSkeleton } from './BlockSkeleton.jsx'
import { useBlockLoader } from './useBlockLoader.js'

/**
 * Bloque con contenido: une el cargador con el esqueleto, el aviso de error o
 * el contenido (RF-40, RF-41, RF-47). Cuando la carga tiene éxito, el
 * contenido sustituye al esqueleto sin ningún aviso adicional.
 *
 * @template T
 * @param {{
 *   blockName: string,
 *   load: () => Promise<T>,
 *   renderContent: (data: T) => import('react').ReactNode,
 *   skeletonShape?: 'generic' | 'strip',
 * }} props
 */
export function AsyncBlock({ blockName, load, renderContent, skeletonShape }) {
  const { state, retry } = useBlockLoader(load)

  if (state.status === 'loading') return <BlockSkeleton shape={skeletonShape} />
  if (state.status === 'error') return <BlockError blockName={blockName} onRetry={retry} />
  return renderContent(state.data)
}
