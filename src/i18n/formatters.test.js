import { describe, expect, it } from 'vitest'
import { formatDate, formatTime } from './formatters.js'

// 21 de septiembre de 2026, 18:30, en hora local.
const sample = new Date(2026, 8, 21, 18, 30)

describe('formateadores (RF-71)', () => {
  it('fecha en español', () => {
    expect(formatDate(sample, 'es')).toBe('21 de septiembre de 2026')
  })

  it('fecha en inglés', () => {
    expect(formatDate(sample, 'en')).toBe('September 21, 2026')
  })

  it('hora en español usa 24 h', () => {
    expect(formatTime(sample, 'es')).toBe('18:30')
  })

  it('hora en inglés usa AM/PM', () => {
    expect(formatTime(sample, 'en')).toMatch(/^6:30\sPM$/)
  })
})
