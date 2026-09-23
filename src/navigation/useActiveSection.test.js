import { describe, expect, it } from 'vitest'
import { buildRouteDefinitions } from '../app/routeDefinitions.js'
import { resolveActiveSectionId } from './useActiveSection.js'

const definitions = buildRouteDefinitions({ devRoutes: [{ path: '/dev/block-demo', kind: 'demo' }] })

// Una subpágina definida en el futuro por una spec de contenido.
const withSubpage = [
  { path: '/players', sectionId: 'players', children: [{ path: ':playerId', kind: 'content' }] },
  { path: '*', kind: 'notFound' },
]

describe('resolveActiveSectionId (RF-24, RF-25)', () => {
  it.each([
    ['/', 'home'],
    ['/players', 'players'],
    ['/ml-models', 'mlModels'],
    ['/players/xyz', null],
    ['/no-existe', null],
    ['/dev/block-demo', null],
  ])('%s → %s', (pathname, expected) => {
    expect(resolveActiveSectionId(pathname, definitions)).toBe(expected)
  })

  it('una subpágina definida activa su sección madre', () => {
    expect(resolveActiveSectionId('/players/scump', withSubpage)).toBe('players')
  })
})
