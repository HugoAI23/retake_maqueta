import { describe, expect, it } from 'vitest'
import { contrastRatio, parseHexColor, relativeLuminance } from './contrast.js'

describe('contraste WCAG (spec 002, plan D-13)', () => {
  it('blanco sobre negro es 21:1 y un color consigo mismo 1:1', () => {
    expect(contrastRatio('#ffffff', '#000000')).toBeCloseTo(21, 5)
    expect(contrastRatio('#0b3d91', '#0b3d91')).toBeCloseTo(1, 5)
  })

  it('es simétrico', () => {
    expect(contrastRatio('#f5d90a', '#222222')).toBeCloseTo(contrastRatio('#222222', '#f5d90a'), 10)
  })

  it('luminancia relativa de referencia', () => {
    expect(relativeLuminance('#ffffff')).toBeCloseTo(1, 5)
    expect(relativeLuminance('#000000')).toBe(0)
  })

  it('acepta #rgb y #rrggbb y rechaza lo demás', () => {
    expect(parseHexColor('#fff')).toEqual([255, 255, 255])
    expect(parseHexColor('#0B3D91')).toEqual([11, 61, 145])
    expect(parseHexColor('red')).toBeNull()
    expect(parseHexColor('#12345')).toBeNull()
    expect(parseHexColor(null)).toBeNull()
  })
})
