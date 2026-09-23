import { describe, expect, it } from 'vitest'
import { homeBlocksRegistry } from './homeBlocksRegistry.js'
import { sectionsRegistry } from './sectionsRegistry.js'

describe('sectionsRegistry (RF-6, RF-8, RF-26, RF-37)', () => {
  it('tiene las ocho secciones en el orden de RF-6', () => {
    expect(sectionsRegistry.map((s) => s.id)).toEqual([
      'home',
      'matches',
      'teams',
      'players',
      'tournaments',
      'standings',
      'news',
      'mlModels',
    ])
  })

  it('solo Modelos de ML está destacada', () => {
    expect(sectionsRegistry.filter((s) => s.featured).map((s) => s.id)).toEqual(['mlModels'])
  })

  it('solo Inicio tiene contenido en la spec 001', () => {
    expect(sectionsRegistry.filter((s) => s.hasContent).map((s) => s.id)).toEqual(['home'])
  })

  it('cada sección tiene una dirección propia y distinta', () => {
    const paths = sectionsRegistry.map((s) => s.path)
    expect(new Set(paths).size).toBe(paths.length)
    expect(paths.every((p) => p.startsWith('/'))).toBe(true)
  })
})

describe('homeBlocksRegistry (RF-38, RF-39)', () => {
  it('tiene los cuatro bloques y ninguno con contenido', () => {
    expect(Object.keys(homeBlocksRegistry)).toEqual(['ticker', 'spotlight', 'news', 'matchGrid'])
    expect(Object.values(homeBlocksRegistry).every((b) => b.hasContent === false)).toBe(true)
  })
})
