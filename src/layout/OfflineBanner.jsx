import { useTranslation } from 'react-i18next'
import { useConnection } from '../connection/ConnectionProvider.jsx'

/**
 * Aviso general "Sin conexión" mientras el dispositivo no tiene red, tanto al
 * abrir Retake como durante la navegación (RF-50, RF-52). La región está
 * siempre montada para que los lectores de pantalla anuncien el cambio.
 */
export function OfflineBanner() {
  const { t } = useTranslation()
  const { isOnline } = useConnection()

  return (
    <div role="status" aria-live="polite" data-testid="offline-banner">
      {!isOnline && (
        <p className="bg-focus px-4 py-2 text-center text-sm font-semibold text-bg">{t('status.offline')}</p>
      )}
    </div>
  )
}
