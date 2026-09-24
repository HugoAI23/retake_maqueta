import { describe, expect, it } from 'vitest'
import { formatLastUpdated, isStale, lastUpdatedOf, STALE_THRESHOLD_MS } from './freshnessRules.js'

describe('última actualización (T-072; RF-155, RF-157 a RF-159)', () => {
  it('es el cambio más reciente de lo que se muestra', () => {
    const items = [{ changedAt: '2026-12-05T19:00:00Z' }, { changedAt: '2026-12-05T20:30:00Z' }, { changedAt: null }]
    expect(lastUpdatedOf(items, '2026-12-01T00:00:00Z')).toBe('2026-12-05T20:30:00Z')
  })

  it('sin datos, es el último cambio del conjunto que vigila el bloque', () => {
    expect(lastUpdatedOf([], '2026-12-01T00:00:00Z')).toBe('2026-12-01T00:00:00Z')
    expect(lastUpdatedOf([], null)).toBeNull()
  })
})

describe('datos sin actualizar (T-072; RF-89, RF-91, RF-92)', () => {
  const now = Date.parse('2026-12-05T20:00:00Z')

  it('lo están si el servidor lo dice', () => {
    expect(isStale({ dataset: 'matches', serverStale: true, cutSince: null, now })).toBe(true)
  })

  it('o si el canal lleva cortado más que el umbral del conjunto', () => {
    expect(isStale({ dataset: 'live', serverStale: false, cutSince: now - STALE_THRESHOLD_MS.live - 1, now })).toBe(true)
    expect(isStale({ dataset: 'live', serverStale: false, cutSince: now - 30_000, now })).toBe(false)
    expect(isStale({ dataset: 'matches', serverStale: false, cutSince: now - 30 * 60_000, now })).toBe(false)
  })

  it('el aviso se retira al volver a actualizarse', () => {
    expect(isStale({ dataset: 'live', serverStale: false, cutSince: null, now })).toBe(false)
  })
})

describe('formato de la última actualización en los dos idiomas (T-072)', () => {
  const t = (key, values) => ({ 'live.lastUpdated': `Actualizado: ${values?.when}`, 'live.neverUpdated': 'Sin actualizar todavía' })[key]

  it('en español', () => {
    expect(formatLastUpdated('2026-12-05T20:00:00Z', 'es', t, 'UTC')).toBe('Actualizado: 5 de diciembre de 2026 a las 20:00')
  })

  it('en inglés', () => {
    const en = (key, values) => ({ 'live.lastUpdated': `Updated: ${values?.when}` })[key]
    expect(formatLastUpdated('2026-12-05T20:00:00Z', 'en', en, 'UTC')).toBe('Updated: December 5, 2026 at 8:00 PM')
  })

  it('sin ningún cambio registrado', () => {
    expect(formatLastUpdated(null, 'es', t)).toBe('Sin actualizar todavía')
  })
})
