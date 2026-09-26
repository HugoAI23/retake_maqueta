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
 * Forma de tabla de datos (spec 004, RF-24): una fila de cabecera y varias
 * filas, cada una con una columna estrecha (posición), una ancha (equipo) y
 * varias de cifras.
 */
const TABLE_ROWS = 6
const TABLE_CELLS = ['w-8', 'flex-1', 'w-12', 'w-12', 'w-12']

/**
 * Esqueleto de carga de un bloque. Se anuncia como "cargando" a los lectores
 * de pantalla (RF-40, RF-79); los marcadores están ocultos a los lectores.
 *
 * @param {{ shape?: keyof typeof SHAPES | 'table' }} props
 */
export function BlockSkeleton({ shape = 'generic' }) {
  const { t } = useTranslation()
  const pulse = 'animate-pulse rounded bg-raised motion-reduce:animate-none'

  if (shape === 'table') {
    return (
      <div role="status" aria-busy="true" className="flex flex-col gap-3" data-testid="block-skeleton" data-shape="table">
        <span className="sr-only">{t('status.loading')}</span>
        {Array.from({ length: TABLE_ROWS + 1 }, (_, row) => (
          <div key={row} aria-hidden="true" data-skeleton-row className="flex items-center gap-4">
            {TABLE_CELLS.map((width, cell) => (
              <div key={cell} data-skeleton-cell className={`${row === 0 ? 'h-3' : 'h-5'} ${pulse} ${width}`} />
            ))}
          </div>
        ))}
      </div>
    )
  }

  const lines = SHAPES[shape] ?? SHAPES.generic

  return (
    <div role="status" aria-busy="true" className="flex flex-col gap-3" data-testid="block-skeleton">
      <span className="sr-only">{t('status.loading')}</span>
      {lines.map((width, index) => (
        <div key={index} aria-hidden="true" className={`h-4 ${pulse} ${width}`} />
      ))}
    </div>
  )
}
