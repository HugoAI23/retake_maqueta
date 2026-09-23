/**
 * Escudo de un equipo (spec 002, RF-14, RF-15, RF-118, RF-127 y RF-128).
 *
 * Decide qué pintar; el tamaño, la forma y el lugar los decide cada spec visual.
 * El logo solo debe pintarse como imagen (`<img>`), nunca de otra forma (RF-130).
 */
import { colors } from '../config/designTokens.js'
import { contrastRatio, parseHexColor } from '../shared/contrast.js'

const WHITE = '#ffffff'
const BLACK = '#000000'

/**
 * Blanco o negro, el que dé más contraste con el fondo (RF-127). Uno de los dos
 * siempre llega a 4,5:1 o más (RF-128).
 * @param {string} background Color `#rrggbb` válido.
 */
export function bestTextColor(background) {
  return contrastRatio(WHITE, background) >= contrastRatio(BLACK, background) ? WHITE : BLACK
}

/**
 * @typedef {{ kind: 'logo', src: string } | { kind: 'abbreviation', text: string, background: string, foreground: string }} TeamBadge
 */

/**
 * Qué pintar como escudo de un equipo con una identidad dada.
 *
 * 1. El logo de esa identidad.
 * 2. Si no tiene, el de la identidad más reciente de la franquicia (RF-14).
 * 3. Si tampoco, la abreviatura sobre el color primario de la identidad, aunque una
 *    identidad anterior tenga logo (RF-15); sin color primario válido, sobre el color
 *    neutro de Retake (RF-118). Sin abreviatura, se usa el nombre corto.
 * @param {import('./leagueApi.js').Identity} identity
 * @param {import('./leagueApi.js').Identity[]} franchiseIdentities Todas las identidades de la franquicia.
 * @returns {TeamBadge}
 */
export function resolveTeamBadge(identity, franchiseIdentities) {
  if (identity.logoUrl) return { kind: 'logo', src: identity.logoUrl }
  const latest = [...franchiseIdentities].sort((a, b) => a.validFrom.localeCompare(b.validFrom)).at(-1)
  if (latest?.logoUrl) return { kind: 'logo', src: latest.logoUrl }

  const background = parseHexColor(identity.primaryColor) ? identity.primaryColor : colors['team-neutral']
  return {
    kind: 'abbreviation',
    text: identity.abbreviation || identity.shortName,
    background,
    foreground: bestTextColor(background),
  }
}
