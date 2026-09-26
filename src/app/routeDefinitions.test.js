import { describe, expect, it } from 'vitest'
import { buildRouteDefinitions } from './routeDefinitions.js'

describe('rutas de las secciones con contenido (spec 004, RF-52)', () => {
  it('Posiciones es una página de contenido y las demás secciones siguen igual', () => {
    const kinds = Object.fromEntries(buildRouteDefinitions().map((r) => [r.path, r.kind]))
    expect(kinds).toMatchObject({
      '/': 'home',
      '/standings': 'content',
      '/matches': 'comingSoon',
      '/teams': 'comingSoon',
      '/players': 'comingSoon',
      '/tournaments': 'comingSoon',
      '/news': 'comingSoon',
      '/ml-models': 'comingSoon',
      '/admin': 'admin',
      '*': 'notFound',
    })
  })
})
