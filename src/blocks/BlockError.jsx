import { useTranslation } from 'react-i18next'
import { AnimatedButton } from '../motion/AnimatedButton.jsx'

/**
 * Aviso de error de un bloque con el botón "Reintentar" (RF-41, RF-44).
 * El nombre accesible del botón incluye el nombre del bloque, para distinguir
 * varios "Reintentar" en la misma página (RF-79).
 *
 * @param {{ blockName: string, onRetry: () => void }} props
 */
export function BlockError({ blockName, onRetry }) {
  const { t } = useTranslation()

  return (
    <div role="alert" className="flex flex-col items-start gap-3">
      <p className="text-danger">{t('status.loadError')}</p>
      <AnimatedButton
        type="button"
        onClick={onRetry}
        aria-label={t('status.retryBlock', { block: blockName })}
        className="min-h-11 rounded-md border border-border bg-raised px-4 font-semibold text-text transition-colors hover:border-accent hover:text-accent active:bg-bg"
      >
        {t('status.retry')}
      </AnimatedButton>
    </div>
  )
}
