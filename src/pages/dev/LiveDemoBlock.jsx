import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocale } from '../../i18n/LocaleProvider.jsx'
import { getMatches } from '../../league/leagueApi.js'
import { formatLastUpdated, lastUpdatedOf } from '../../live/freshnessRules.js'
import { useAnnouncer } from '../../live/LiveAnnouncer.jsx'
import { LiveBlock } from '../../live/LiveBlock.jsx'
import { useDatasetFreshness } from '../../live/LiveProvider.jsx'
import { demoDictionary } from './demoDictionary.js'

/**
 * Bloque de demostración en vivo (spec 003, T-074; plan I-30). SOLO DESARROLLO: vive en la página
 * de demostración, fuera del menú y fuera del paquete de producción (RF-95 de la 001).
 *
 * Sirve para verificar a mano la actualización automática, la hora de última actualización, el
 * aviso de datos sin actualizar y los anuncios en vivo mientras ninguna spec visual los use.
 *
 * @param {{ loadMatches?: () => Promise<object[]> }} props
 */
export function LiveDemoBlock({ loadMatches = getMatches }) {
  const { t, i18n } = useTranslation()
  useState(() => {
    for (const [lang, texts] of Object.entries(demoDictionary)) {
      i18n.addResourceBundle(lang, 'translation', { demo: texts }, true, true)
    }
  })
  const [load] = useState(() => () => loadMatches().then((matches) => matches.filter((m) => m.status === 'live')))

  return (
    <section data-testid="live-demo" className="flex flex-col gap-3 rounded-xl border border-border bg-surface p-6"
             aria-labelledby="live-demo-heading">
      <h2 id="live-demo-heading" className="text-xl font-bold">{t('demo.live.heading')}</h2>
      <p className="text-muted">{t('demo.live.intro')}</p>
      <LiveBlock blockName={t('demo.live.blockName')} load={load} datasets={['live', 'matches']} cycle="live"
                 renderContent={(matches) => <LiveMatches matches={matches} />} />
    </section>
  )
}

const teamName = (slot) => slot?.identity?.shortName ?? '—'
const scoreLine = (match) =>
  `${teamName(match.slots[0])} ${match.mapsWon?.[0] ?? 0} - ${match.mapsWon?.[1] ?? 0} ${teamName(match.slots[1])}`

function LiveMatches({ matches }) {
  const { t } = useTranslation()
  const { locale } = useLocale()
  const announce = useAnnouncer()
  const live = useDatasetFreshness('live')
  const previous = useRef(new Map())

  // Anuncia solo los cambios de marcador de los partidos en vivo (RF-94 a RF-96).
  useEffect(() => {
    for (const match of matches) {
      const line = scoreLine(match)
      const before = previous.current.get(match.id)
      if (before !== undefined && before !== line) announce(line, { dataset: 'live' })
      previous.current.set(match.id, line)
    }
  }, [matches, announce])

  const stale = live.stale || matches.some((match) => match.isStale)
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm text-muted">{formatLastUpdated(lastUpdatedOf(matches, live.lastChangedAt), locale, t)}</p>
      {stale && <p className="rounded-md border border-border bg-raised p-2 text-sm">{t('live.stale')}</p>}
      {matches.length === 0 ? <p>{t('demo.live.empty')}</p> : (
        <ul className="flex flex-col gap-2">
          {matches.map((match) => (
            <li key={match.id} className="rounded-md border border-border p-3">
              <p className="text-lg font-bold">{scoreLine(match)}</p>
              {match.liveMap && (
                <p className="text-muted">{match.liveMap.mode} · {match.liveMap.score?.join(' - ')}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
