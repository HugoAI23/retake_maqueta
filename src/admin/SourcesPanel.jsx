import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AsyncBlock } from '../blocks/AsyncBlock.jsx'
import { useConnection } from '../connection/ConnectionProvider.jsx'
import { useLocale } from '../i18n/LocaleProvider.jsx'
import { getSources, refreshSource } from './adminApi.js'
import { RequestResult } from './RequestResult.jsx'

/**
 * Estado de las fuentes y peticiones de actualización (spec 003: RF-100 a RF-116; C-19).
 *
 * @param {{ guard: <T>(load: () => Promise<T>) => () => Promise<T>, onShowLog: (source: string) => void,
 *   onAuthLost: (error: Error) => void }} props
 */
export function SourcesPanel({ guard, onShowLog, onAuthLost }) {
  const { t } = useTranslation()
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-surface p-6" aria-labelledby="admin-sources">
      <h2 id="admin-sources" className="text-xl font-bold">{t('admin.sources.heading')}</h2>
      <AsyncBlock
        blockName={t('admin.sources.blockName')}
        load={guard(getSources)}
        renderContent={(sources) => (
          <ul className="flex flex-col gap-4">
            {sources.map((source) => (
              <SourceRow key={source.source} source={source} onShowLog={onShowLog} onAuthLost={onAuthLost} />
            ))}
          </ul>
        )}
      />
    </section>
  )
}

function SourceRow({ source, onShowLog, onAuthLost }) {
  const { t } = useTranslation()
  const { formatDateTime } = useLocale()
  const { isOnline } = useConnection()
  const [request, setRequest] = useState(source.activeRequest)
  const [failed, setFailed] = useState(false)
  const name = t(`admin.sources.name.${source.source}`)
  const when = (iso) => (iso ? formatDateTime(new Date(iso)) : t('admin.sources.never'))
  const isWiki = source.source === 'wiki'

  const refresh = async () => {
    setFailed(false)
    try {
      setRequest(await refreshSource(source.source))
    } catch (error) {
      if (error?.status === 401) onAuthLost(error)
      else setFailed(true)
    }
  }

  return (
    <li data-testid={`source-${source.source}`} className="flex flex-col gap-2 border-b border-border pb-4 last:border-0">
      <p className="flex flex-wrap items-center gap-2 font-semibold">
        {name}
        {source.stopped && (
          <span className="rounded-md border border-border px-2 text-sm text-text">{t('admin.sources.stopped')}</span>
        )}
      </p>
      <dl className="grid grid-cols-1 gap-x-4 text-sm sm:grid-cols-[auto_1fr]">
        {isWiki ? (
          <>
            <dt className="text-muted">{t('admin.sources.lastImport')}</dt>
            <dd>{when(source.lastSuccessAt)}</dd>
          </>
        ) : (
          <>
            <dt className="text-muted">{t('admin.sources.lastAttempt')}</dt>
            <dd>{when(source.lastAttemptAt)}</dd>
            <dt className="text-muted">{t('admin.sources.lastSuccess')}</dt>
            <dd>{when(source.lastSuccessAt)}</dd>
          </>
        )}
      </dl>
      {source.refreshable ? (
        <div className="flex flex-col gap-2">
          <button type="button" onClick={refresh} disabled={!isOnline || (request && request.status !== 'done')}
                  className="min-h-11 self-start rounded-md border border-border bg-raised px-4 font-semibold hover:border-accent hover:text-accent disabled:opacity-60">
            {t('admin.sources.refresh', { source: name })}
          </button>
          {!isOnline && <p className="text-sm text-muted">{t('admin.sources.offline')}</p>}
          {failed && <p role="alert" className="text-sm">{t('admin.request.failed')}</p>}
          {request && (
            <RequestResult key={request.id} request={request} onShowLog={() => onShowLog(source.source)}
                           onAuthLost={onAuthLost} />
          )}
        </div>
      ) : (
        <p className="text-sm text-muted">{t(`admin.sources.reason.${source.source}`)}</p>
      )}
    </li>
  )
}
