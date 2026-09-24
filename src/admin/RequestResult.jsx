import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getRequest } from './adminApi.js'

/** Cada cuánto se pregunta por una petición en curso. */
export const REQUEST_POLL_MS = 2000

/**
 * Resultado de una petición de actualización: en curso, éxito, parcial o fallo, con su número de
 * incidencias y acceso a ellas en el registro (spec 003: RF-103 a RF-106, RF-109).
 *
 * @param {{ request: object, onShowLog: () => void, onAuthLost: (error: Error) => void }} props
 */
export function RequestResult({ request: initial, onShowLog, onAuthLost }) {
  const { t } = useTranslation()
  const [request, setRequest] = useState(initial)

  useEffect(() => {
    if (request.status === 'done') return undefined
    const timer = setTimeout(() => {
      getRequest(request.id).then(setRequest).catch((error) => onAuthLost(error))
    }, REQUEST_POLL_MS)
    return () => clearTimeout(timer)
  }, [request, onAuthLost])

  const label = request.status === 'done' ? t(`admin.request.${request.result}`) : t(`admin.request.${request.status}`)
  return (
    <div className="flex flex-col gap-1 text-sm" aria-live="polite">
      {initial.alreadyRunning && <p>{t('admin.request.alreadyRunning')}</p>}
      <p className="font-semibold">{label}</p>
      {request.status === 'done' && (
        <p>
          {t('admin.request.incidents', { count: request.incidentCount ?? 0 })}{' '}
          <button type="button" onClick={onShowLog} className="min-h-11 underline hover:text-accent">
            {t('admin.request.viewLog')}
          </button>
        </p>
      )}
    </div>
  )
}
