import { useTranslation } from 'react-i18next'

/**
 * Formas de esqueleto disponibles. Cada spec de contenido podrá añadir la
 * suya para que el esqueleto se parezca a su contenido (RF-40).
 */
const SHAPES = {
  generic: ['w-2/3', 'w-full', 'w-5/6', 'w-1/2'],
  strip: ['w-1/3'],
}

/**
 * Esqueleto de carga de un bloque. Se anuncia como "cargando" a los lectores
 * de pantalla (RF-40, RF-79).
 *
 * @param {{ shape?: keyof typeof SHAPES }} props
 */
export function BlockSkeleton({ shape = 'generic' }) {
  const { t } = useTranslation()
  const lines = SHAPES[shape] ?? SHAPES.generic

  return (
    <div role="status" aria-busy="true" className="flex flex-col gap-3" data-testid="block-skeleton">
      <span className="sr-only">{t('status.loading')}</span>
      {lines.map((width, index) => (
        <div key={index} aria-hidden="true" className={`h-4 animate-pulse rounded bg-raised motion-reduce:animate-none ${width}`} />
      ))}
    </div>
  )
}
