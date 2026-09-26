import { describe, expect, it } from 'vitest'
import { diffTone, formatDiff, formatNumber, formatRecord } from './tableFormat.js'

const MINUS = '−'
const EN_DASH = '–'

describe('formato de las cifras de las tablas (spec 004, RF-20 a RF-23)', () => {
  it('balance ganados–perdidos con una raya entre las cifras', () => {
    expect(formatRecord({ won: 12, lost: 5 }, 'es')).toBe(`12${EN_DASH}5`)
    expect(formatRecord({ won: 0, lost: 0 }, 'en')).toBe(`0${EN_DASH}0`)
  })

  it('diferencia positiva con +, negativa con − (U+2212) y 0 sin signo, en los dos idiomas', () => {
    for (const locale of ['es', 'en']) {
      expect(formatDiff(8, locale)).toBe('+8')
      expect(formatDiff(-3, locale)).toBe(`${MINUS}3`)
      expect(formatDiff(0, locale)).toBe('0')
      expect(formatDiff(-0, locale)).toBe('0')
      expect(formatDiff(-3, locale)).not.toContain('-')
    }
  })

  it('los dígitos siguen el formato del idioma; el signo, no', () => {
    expect(formatNumber(12345, 'es')).toBe('12.345')
    expect(formatNumber(12345, 'en')).toBe('12,345')
    expect(formatDiff(-12345, 'es')).toBe(`${MINUS}12.345`)
    expect(formatDiff(12345, 'en')).toBe('+12,345')
    expect(formatRecord({ won: 12345, lost: 2 }, 'en')).toBe(`12,345${EN_DASH}2`)
  })

  it('tono de la diferencia: positivo, negativo o el del texto normal en el 0', () => {
    expect(diffTone(3)).toBe('positive')
    expect(diffTone(-1)).toBe('negative')
    expect(diffTone(0)).toBe('neutral')
  })
})
