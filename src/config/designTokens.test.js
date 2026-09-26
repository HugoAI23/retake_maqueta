import { describe, expect, it } from 'vitest'
import { contrastRatio } from '../shared/contrast.js'
import { colors, contrastPairs } from './designTokens.js'

describe('variables de diseño (RF-74)', () => {
  it.each(contrastPairs)('%s sobre %s alcanza 4,5:1', (fg, bg) => {
    expect(contrastRatio(colors[fg], colors[bg])).toBeGreaterThanOrEqual(4.5)
  })
})

describe('colores de las tablas de datos (spec 004, RF-22, RF-30, RF-35)', () => {
  // Diferencia positiva sobre los fondos de la tabla, y los tres colores
  // de la diferencia sobre el fondo del resaltado de una celda que cambia.
  const tablePairs = [
    ['positive', 'surface'],
    ['positive', 'bg'],
    ['text', 'highlight'],
    ['positive', 'highlight'],
    ['danger', 'highlight'],
  ]

  it.each(tablePairs)('%s sobre %s está declarada y alcanza 4,5:1', (fg, bg) => {
    expect(contrastPairs).toContainEqual([fg, bg])
    expect(colors[fg]).toBeDefined()
    expect(colors[bg]).toBeDefined()
    expect(contrastRatio(colors[fg], colors[bg])).toBeGreaterThanOrEqual(4.5)
  })
})
