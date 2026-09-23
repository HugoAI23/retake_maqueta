import { useTranslation } from 'react-i18next'

/**
 * Hueco de un bloque cuya spec de contenido aún no está implementada:
 * su nombre y "Próximamente", sin esqueleto ni error (RF-38, RF-39).
 *
 * @param {{ blockId: string, compact?: boolean }} props `compact` para la franja de la cinta.
 */
export function ComingSoonBlock({ blockId, compact = false }) {
  const { t } = useTranslation()

  if (compact) {
    return (
      <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span className="font-semibold text-text">{t(`blocks.${blockId}`)}</span>
        <span className="text-muted">{t('status.comingSoon')}</span>
      </p>
    )
  }

  return (
    <div className="flex h-full min-h-40 flex-col items-center justify-center gap-2 rounded-xl border border-border bg-surface p-6 text-center">
      <h2 className="text-lg font-bold">{t(`blocks.${blockId}`)}</h2>
      <p className="rounded-full bg-raised px-3 py-1 text-sm font-semibold text-muted">{t('status.comingSoon')}</p>
    </div>
  )
}
