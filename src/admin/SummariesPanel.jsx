import { useTranslation } from 'react-i18next'
import { AsyncBlock } from '../blocks/AsyncBlock.jsx'
import { useLocale } from '../i18n/LocaleProvider.jsx'
import { getSummaries } from './adminApi.js'

/**
 * Resúmenes diarios de los últimos 7 días (spec 003: RF-150 a RF-154). Por fuente: consultas
 * fallidas, datos rechazados y cada incidencia distinta del día con sus repeticiones y acceso a su
 * detalle en el registro (RF-151, RF-152).
 * @param {{ guard: Function, onShowLog: (source: string) => void }} props
 */
export function SummariesPanel({ guard, onShowLog }) {
  const { t } = useTranslation()
  const { formatDate } = useLocale()
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-surface p-6" aria-labelledby="admin-summaries">
      <h2 id="admin-summaries" className="text-xl font-bold">{t('admin.summaries.heading')}</h2>
      <AsyncBlock
        blockName={t('admin.summaries.blockName')}
        load={guard(getSummaries)}
        renderContent={(summaries) => summaries.length === 0 ? <p className="text-muted">{t('admin.summaries.empty')}</p> : (
          <ul className="flex flex-col gap-2 text-sm">
            {summaries.map((summary) => (
              <li key={summary.day} className="rounded-md border border-border p-3">
                <p className="font-semibold">{formatDate(new Date(`${summary.day}T12:00:00`))}</p>
                <p>{t('admin.summaries.totals', {
                  incidents: summary.content.total_incidents ?? 0,
                  failed: summary.content.total_failed_queries ?? 0,
                  rejected: summary.content.total_rejected_data ?? 0,
                })}</p>
                {Object.entries(summary.content.by_source ?? {}).map(([source, detail]) => (
                  <div key={source} className="mt-2 flex flex-col gap-1">
                    <p className="font-semibold">
                      {t('admin.summaries.bySource', {
                        source: source === 'system' ? t('admin.summaries.system') : t(`admin.sources.name.${source}`),
                        failed: detail.failed_queries ?? 0, rejected: detail.rejected_data ?? 0,
                      })}
                    </p>
                    <ul className="flex flex-col gap-1">
                      {(detail.incidents ?? []).map((incident) => (
                        <li key={incident.id} className="break-words">
                          {incident.kind} · {incident.subject} · {incident.reason} · {t('admin.log.repetitions', { count: incident.repetitions })}
                        </li>
                      ))}
                    </ul>
                    {source !== 'system' && (
                      <button type="button" onClick={() => onShowLog(source)} className="min-h-11 self-start underline hover:text-accent">
                        {t('admin.request.viewLog')}
                      </button>
                    )}
                  </div>
                ))}
              </li>
            ))}
          </ul>
        )}
      />
    </section>
  )
}
