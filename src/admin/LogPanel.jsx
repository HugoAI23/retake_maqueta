import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AsyncBlock } from '../blocks/AsyncBlock.jsx'
import { useLocale } from '../i18n/LocaleProvider.jsx'
import { getLog } from './adminApi.js'

const PAGE_SIZE = 50

/**
 * Registro de los últimos 7 días (spec 003: RF-118 a RF-120, RF-140 a RF-149). Los mensajes de las
 * fuentes se muestran sin traducir y como texto plano: React escapa todo lo que pinta.
 *
 * @param {{ guard: Function, source: string, onSourceChange: (source: string) => void }} props
 */
export function LogPanel({ guard, source, onSourceChange }) {
  const { t } = useTranslation()
  const [page, setPage] = useState(1)
  return (
    <section id="admin-log" className="flex flex-col gap-3 rounded-xl border border-border bg-surface p-6" aria-labelledby="admin-log-heading">
      <h2 id="admin-log-heading" className="text-xl font-bold">{t('admin.log.heading')}</h2>
      <label className="flex items-center gap-2 text-sm font-semibold">
        {t('admin.log.source')}
        <select value={source} onChange={(e) => { setPage(1); onSourceChange(e.target.value) }}
                className="min-h-11 rounded-md border border-border bg-bg px-2 text-text">
          <option value="">{t('admin.log.all')}</option>
          {['bp', 'wiki', 'cdl'].map((id) => <option key={id} value={id}>{t(`admin.sources.name.${id}`)}</option>)}
        </select>
      </label>
      <AsyncBlock
        key={`${source}-${page}`}
        blockName={t('admin.log.blockName')}
        load={guard(() => getLog({ source: source || undefined, page, pageSize: PAGE_SIZE }))}
        renderContent={(log) => <LogEntries log={log} page={page} onPage={setPage} />}
      />
    </section>
  )
}

function LogEntries({ log, page, onPage }) {
  const { t } = useTranslation()
  const { formatDateTime } = useLocale()
  const when = (iso) => formatDateTime(new Date(iso))
  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-semibold">{t('admin.log.incidents')}</h3>
      {log.incidents.length === 0 ? <p className="text-muted">{t('admin.log.empty')}</p> : (
        <ul className="flex flex-col gap-2 text-sm">
          {log.incidents.map((incident) => (
            <li key={incident.id} className="rounded-md border border-border p-3">
              <p className="font-semibold">{incident.kind} · {incident.source ?? '—'} · {incident.subject}</p>
              <p className="break-words">{incident.reason}</p>
              <p className="text-muted">
                {t('admin.log.repetitions', { count: incident.repetitions })} · {t('admin.log.lastAt', { when: when(incident.lastAt) })}
              </p>
            </li>
          ))}
        </ul>
      )}
      <h3 className="font-semibold">{t('admin.log.runs')}</h3>
      {log.runs.length === 0 ? <p className="text-muted">{t('admin.log.empty')}</p> : (
        <ul className="flex flex-col gap-2 text-sm">
          {log.runs.map((run) => (
            <li key={run.id} className="rounded-md border border-border p-3">
              <p className="font-semibold">{run.source} · {run.job} · {run.outcome} · {when(run.finishedAt)}</p>
              {run.message && <p className="break-words">{run.message}</p>}
            </li>
          ))}
        </ul>
      )}
      <div className="flex gap-2">
        <button type="button" disabled={page === 1} onClick={() => onPage(page - 1)}
                className="min-h-11 rounded-md border border-border px-4 disabled:opacity-60">{t('admin.log.previous')}</button>
        <button type="button" disabled={log.runs.length < log.pageSize && log.incidents.length < log.pageSize}
                onClick={() => onPage(page + 1)}
                className="min-h-11 rounded-md border border-border px-4 disabled:opacity-60">{t('admin.log.next')}</button>
      </div>
    </div>
  )
}
