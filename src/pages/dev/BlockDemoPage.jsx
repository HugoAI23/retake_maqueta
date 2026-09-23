import { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AsyncBlock } from '../../blocks/AsyncBlock.jsx'
import { useLocale } from '../../i18n/LocaleProvider.jsx'
import { usePageTitle } from '../../shared/usePageTitle.js'
import { demoDictionary } from './demoDictionary.js'
import { createDemoLoad, DEMO_SCENARIOS } from './demoScenarios.js'

/**
 * Página de demostración de bloques (RF-89 a RF-93).
 *
 * SOLO DESARROLLO: la ruta únicamente se registra en el modo de desarrollo de
 * Vite y este archivo no entra en la versión de producción (RF-95, plan D-13).
 * No tiene entrada en el menú (RF-94).
 */
export default function BlockDemoPage() {
  const { t, i18n } = useTranslation()
  const { formatDateTime } = useLocale()
  // Registra los textos de la demostración antes del primer render.
  useState(() => {
    for (const [lang, texts] of Object.entries(demoDictionary)) {
      i18n.addResourceBundle(lang, 'translation', { demo: texts }, true, true)
    }
  })
  const [scenario, setScenario] = useState('ok')
  const [restartKey, setRestartKey] = useState(0)
  const [loadCount, setLoadCount] = useState(0)
  usePageTitle(t('demo.title'))

  const load = useCallback(() => {
    setLoadCount((count) => count + 1)
    return createDemoLoad(scenario)()
  }, [scenario])

  const restart = () => {
    setLoadCount(0)
    setRestartKey((key) => key + 1)
  }

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">{t('demo.title')}</h1>
        <p className="text-muted">{t('demo.intro')}</p>
      </header>

      <fieldset className="flex flex-col gap-2 rounded-xl border border-border p-4">
        <legend className="px-1 font-semibold">{t('demo.scenarioLabel')}</legend>
        {DEMO_SCENARIOS.map((id) => (
          <label key={id} className="flex min-h-11 cursor-pointer items-center gap-2 rounded-md px-2 hover:bg-raised">
            <input
              type="radio"
              name="demo-scenario"
              value={id}
              checked={scenario === id}
              onChange={() => {
                setScenario(id)
                restart()
              }}
              className="size-4 accent-accent"
            />
            {t(`demo.scenarios.${id}`)}
          </label>
        ))}
        <button
          type="button"
          onClick={restart}
          className="mt-2 min-h-11 self-start rounded-md border border-border bg-raised px-4 font-semibold hover:border-accent hover:text-accent active:bg-bg"
        >
          {t('demo.restart')}
        </button>
      </fieldset>

      <p data-testid="demo-load-count" className="text-sm text-muted">
        {t('demo.loadCount', { count: loadCount })}
      </p>

      <div data-testid="demo-block" className="min-h-40 rounded-xl border border-border bg-surface p-6">
        <AsyncBlock
          key={`${scenario}-${restartKey}`}
          blockName={t('demo.blockName')}
          load={load}
          renderContent={(data) => (
            <article className="flex flex-col gap-2">
              <h2 className="text-lg font-bold">{t('demo.sampleHeading')}</h2>
              <p className="text-2xl font-black">
                {data.home} <span className="text-muted">vs</span> {data.away}
              </p>
              <p className="text-muted">{data.event}</p>
              <p>{formatDateTime(data.startsAt)}</p>
              <dl className="grid grid-cols-[auto_1fr] gap-x-4">
                <dt className="text-muted">{t('demo.sampleMode')}</dt>
                <dd>{data.mode}</dd>
                <dt className="text-muted">{t('demo.sampleMap')}</dt>
                <dd>{data.map}</dd>
              </dl>
            </article>
          )}
        />
      </div>
    </section>
  )
}
