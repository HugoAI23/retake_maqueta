import { describe, expect, it } from 'vitest'
import { contrastRatio } from '../shared/contrast.js'
import { colors, contrastPairs } from './designTokens.js'

describe('variables de diseño (RF-74)', () => {
  it.each(contrastPairs)('%s sobre %s alcanza 4,5:1', (fg, bg) => {
    expect(contrastRatio(colors[fg], colors[bg])).toBeGreaterThanOrEqual(4.5)
  })
})
