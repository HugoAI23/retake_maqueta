import { resolveTeamBadge } from '../league/teamBadge.js'
import { TruncatedName } from './TruncatedName.jsx'
import { useIsWide } from './useIsWide.js'

/**
 * Insignia de un equipo (spec 004, §2.2): el logo como imagen, o la abreviatura sobre su
 * color (RF-14, RF-15 y RF-118 de la 002). Es decorativa: el nombre del equipo va al lado.
 *
 * @param {{ badge: import('../league/teamBadge.js').TeamBadge }} props
 */
function TeamBadge({ badge }) {
  if (badge.kind === 'logo') {
    // Solo como <img> (RF-130 de la 002).
    return <img src={badge.src} alt="" className="h-6 w-6 shrink-0 object-contain" />
  }
  return (
    <span
      data-testid="team-badge"
      aria-hidden="true"
      style={{ backgroundColor: badge.background, color: badge.foreground }}
      className="inline-flex h-6 min-w-6 shrink-0 items-center justify-center rounded px-1 text-[10px] font-bold leading-none"
    >
      {badge.text}
    </span>
  )
}

/**
 * Equipo en una tabla de datos (spec 004, §2.2, RF-14 a RF-18).
 *
 * - Desde 1024 px: insignia y nombre corto, que se recorta si no cabe (RF-14, RF-17).
 * - Por debajo: insignia y abreviatura (RF-15).
 * - El nombre legible por los lectores es siempre el nombre corto (RF-16).
 * - Es texto, sin enlace, mientras no existan las fichas de equipo (RF-18).
 *
 * @param {{
 *   identity: import('../league/leagueApi.js').Identity,
 *   identities?: import('../league/leagueApi.js').Identity[],
 * }} props `identities`: todas las de la franquicia, para el respaldo del logo.
 */
export function TeamCell({ identity, identities }) {
  const isWide = useIsWide()
  const badge = resolveTeamBadge(identity, identities ?? [identity])
  const abbreviation = identity.abbreviation || identity.shortName

  return (
    <span data-testid="team-cell" className="flex min-w-0 items-center gap-2">
      <TeamBadge badge={badge} />
      {isWide ? (
        <TruncatedName text={identity.shortName} className="max-w-56" />
      ) : (
        <>
          <span aria-hidden="true">{abbreviation}</span>
          <span className="sr-only">{identity.shortName}</span>
        </>
      )}
    </span>
  )
}
