import { useCallback, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocale } from '../i18n/LocaleProvider.jsx'
import { getFranchises, getStandings } from '../league/leagueApi.js'
import { leagueText } from '../league/labels.js'
import { isStandingsAvailable, standingsUnavailableText } from '../league/standingsRules.js'
import { formatLastUpdated, lastUpdatedOf } from '../live/freshnessRules.js'
import { LiveBlock } from '../live/LiveBlock.jsx'
import { useDatasetFreshness } from '../live/LiveProvider.jsx'
import { useCurrentSeason } from '../live/useCurrentSeason.js'
import { usePageTitle } from '../shared/usePageTitle.js'
import { CountUp } from '../tables/CountUp.jsx'
import { DataTable } from '../tables/DataTable.jsx'
import { diffTone, formatDiff, formatNumber, formatRecord } from '../tables/tableFormat.js'
import { TeamCell } from '../tables/TeamCell.jsx'
import { useIsWide } from '../tables/useIsWide.js'
import { useSortState } from '../tables/useSortState.js'

/** Conjuntos de datos de los que depende la tabla (RF-53a): la tabla y los partidos. */
const DATASETS = ['standings', 'matches']

/** Carga de la sección: filas de la tabla e identidades de cada franquicia (respaldo del logo). */
async function loadStandings() {
  const [rows, franchises] = await Promise.all([getStandings(), getFranchises()])
  return { rows, identitiesByFranchise: new Map(franchises.map((f) => [f.id, f.identities])) }
}

/**
 * Veces que ha cambiado la temporada actual con la página abierta (RF-51a). La llegada del
 * primer año al abrir la página no cuenta: así no se pierde el orden recuperado con Atrás o
 * Adelante (RF-11).
 * @param {number | null} year
 */
function useSeasonChanges(year) {
  const [seen, setSeen] = useState({ year, changes: 0 })
  if (year !== null && year !== seen.year) {
    setSeen({ year, changes: seen.year === null ? seen.changes : seen.changes + 1 })
  }
  return seen.changes
}

/** El más reciente de dos instantes ISO, o el que exista. */
function latest(a, b) {
  if (!a || !b) return a ?? b ?? null
  return Date.parse(a) >= Date.parse(b) ? a : b
}

/**
 * Tabla de posiciones con su última actualización y su aviso de datos sin actualizar.
 *
 * @param {{ data: Awaited<ReturnType<typeof loadStandings>>, year: number | null, seasonChanges: number }} props
 */
function StandingsContent({ data, year, seasonChanges }) {
  const { t } = useTranslation()
  const { locale } = useLocale()
  const standings = useDatasetFreshness('standings')
  const matches = useDatasetFreshness('matches')
  // Con una temporada nueva, orden por defecto (RF-51a).
  const [sortState, setSortState] = useSortState('standings', seasonChanges)

  const available = isStandingsAvailable(data.rows)
  // Sin temporada actual no hay tabla: solo el título y el texto de RF-51 (RF-42a). Con tabla,
  // se muestra aunque el año del pie aún no haya llegado.
  if (year === null && !available) return <p className="text-muted">{standingsUnavailableText(t)}</p>

  const shown = available ? data.rows : []
  // RF-53e: las filas ya traen el cambio de sus partidos contados (plan D-7); sin filas,
  // el último cambio de los dos conjuntos vigilados.
  const updatedAt = lastUpdatedOf(shown, latest(standings.lastChangedAt, matches.lastChangedAt))

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <p className="text-sm text-muted">{formatLastUpdated(updatedAt, locale, t)}</p>
        {(standings.stale || matches.stale) && (
          <p className="rounded-md border border-border bg-raised p-2 text-sm">{t('live.stale')}</p>
        )}
      </div>
      {available ? (
        // Con una temporada nueva es otra tabla: vuelve a hacer su entrada (RF-28, RF-51a).
        <StandingsTable
          key={seasonChanges}
          rows={shown}
          data={data}
          year={year}
          sortState={sortState}
          onSortChange={setSortState}
        />
      ) : (
        <p className="text-muted">{standingsUnavailableText(t)}</p>
      )}
    </div>
  )
}

/** Tono de color de ±Mapas (RF-22): la diferencia se distingue también por el color. */
const DIFF_TONE_CLASS = { positive: 'text-positive', negative: 'text-danger', neutral: 'text-text' }

/**
 * Tabla de posiciones de la temporada (RF-41 a RF-50b).
 *
 * @param {{
 *   rows: import('../league/leagueApi.js').StandingRow[],
 *   data: { identitiesByFranchise: Map<string, import('../league/leagueApi.js').Identity[]> },
 *   year: number | null,
 *   sortState: import('../tables/sortCycle.js').SortState,
 *   onSortChange: (state: import('../tables/sortCycle.js').SortState) => void,
 * }} props
 */
function StandingsTable({ rows, data, year, sortState, onSortChange }) {
  const { t } = useTranslation()
  const { locale } = useLocale()
  const isWide = useIsWide()
  const notAvailable = leagueText(t, 'notAvailable')

  // Texto con el que se ve cada equipo: el orden alfabético va por él (RF-14, RF-15, RF-47, RF-49).
  const shownName = useCallback(
    (row) => (row.identity ? (isWide ? row.identity.shortName : row.identity.abbreviation || row.identity.shortName) : null),
    [isWide],
  )

  // Posiciones que comparten varios equipos (RF-48).
  const shared = useMemo(() => {
    const counts = new Map()
    for (const row of rows) if (row.position !== null) counts.set(row.position, (counts.get(row.position) ?? 0) + 1)
    return new Set([...counts].filter(([, count]) => count > 1).map(([position]) => position))
  }, [rows])

  // Orden por defecto (RF-47): posición de menor a mayor, sin posición al final y, a igualdad,
  // alfabético por el texto que se ve.
  const defaultOrder = useMemo(() => {
    const collator = new Intl.Collator(locale, { sensitivity: 'base', numeric: true })
    return (a, b) => {
      if (a.position !== b.position) {
        if (a.position === null) return 1
        if (b.position === null) return -1
        return a.position - b.position
      }
      return collator.compare(shownName(a) ?? '', shownName(b) ?? '')
    }
  }, [locale, shownName])

  const columns = useMemo(() => {
    const mapDiff = (row) => (row.maps ? row.maps.won - row.maps.lost : null)
    const record = (value) =>
      value ? <CountUp value={value} format={(v) => formatRecord(v, locale)} /> : notAvailable
    return [
      {
        id: 'position',
        header: t('tables.columns.position'),
        sortKind: 'ascending',
        value: (row) => row.position,
        render: (row) => {
          if (row.position === null) return notAvailable
          const number = formatNumber(row.position, locale)
          if (!shared.has(row.position)) return number
          return (
            <>
              <span aria-hidden="true">{number}</span>
              <span className="sr-only">{t('tables.sharedPosition', { position: number })}</span>
            </>
          )
        },
        sticky: true,
      },
      {
        id: 'team',
        header: t('tables.columns.team'),
        sortKind: 'text',
        value: shownName,
        render: (row) =>
          row.identity ? (
            <TeamCell identity={row.identity} identities={data.identitiesByFranchise.get(row.franchiseId)} />
          ) : (
            notAvailable
          ),
        sticky: true,
        rowHeader: true,
      },
      {
        id: 'points',
        header: t('tables.columns.points'),
        sortKind: 'descending',
        countUp: true,
        align: 'end',
        value: (row) => row.points,
        render: (row) =>
          row.points === null ? notAvailable : <CountUp value={row.points} format={(v) => formatNumber(v, locale)} />,
      },
      {
        id: 'series',
        header: t('tables.columns.series'),
        sortKind: 'record',
        countUp: true,
        align: 'end',
        value: (row) => row.series,
        render: (row) => record(row.series),
      },
      {
        id: 'maps',
        header: t('tables.columns.maps'),
        sortKind: 'record',
        countUp: true,
        align: 'end',
        value: (row) => row.maps,
        render: (row) => record(row.maps),
      },
      {
        id: 'mapDiff',
        header: t('tables.columns.mapDiff'),
        sortKind: 'descending',
        countUp: true,
        align: 'end',
        value: mapDiff,
        render: (row) => {
          const diff = mapDiff(row)
          if (diff === null) return notAvailable
          return (
            <span className={DIFF_TONE_CLASS[diffTone(diff)]}>
              <CountUp value={diff} format={(v) => formatDiff(v, locale)} />
            </span>
          )
        },
      },
    ]
  }, [t, locale, data, shared, shownName, notAvailable])

  return (
    <DataTable
      caption={t('tables.caption.standings', { year })}
      columns={columns}
      rows={rows}
      rowKey={(row) => row.franchiseId}
      defaultOrder={defaultOrder}
      sortState={sortState}
      onSortChange={onSortChange}
    />
  )
}

/**
 * Sección Posiciones (spec 004, §2.7): tabla de posiciones de la temporada actual.
 *
 * - Título, "Temporada <año>" con el año del pie y título de la pestaña (RF-42 a RF-42b).
 * - La tabla es un bloque que se actualiza solo con la tabla y los partidos (RF-24 a RF-27,
 *   RF-53a, RF-53b), con su última actualización y el aviso de datos sin actualizar (RF-53c
 *   a RF-53e). Sus cambios no se anuncian a los lectores (RF-53).
 */
export function StandingsPage() {
  const { t } = useTranslation()
  const title = t('sections.standings')
  usePageTitle(title)
  const year = useCurrentSeason()
  const seasonChanges = useSeasonChanges(year)
  const load = useCallback(() => loadStandings(), [])

  return (
    <section data-testid="standings-page" className="mx-auto flex w-full max-w-5xl flex-col gap-4 py-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold">{title}</h1>
        {year !== null && <p className="text-lg text-muted">{t('standings.season', { year })}</p>}
      </div>
      <LiveBlock
        blockName={title}
        load={load}
        datasets={DATASETS}
        skeletonShape="table"
        renderContent={(data) => <StandingsContent data={data} year={year} seasonChanges={seasonChanges} />}
      />
    </section>
  )
}
