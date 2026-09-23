import { describe, expect, it } from 'vitest'
import { getInitialLocale } from './getInitialLocale.js'
import { LOCALE_STORAGE_KEY, readStoredLocale, saveLocale } from './localeStorage.js'
import { resolveInitialLocale } from './resolveInitialLocale.js'

function memoryStorage(initial = {}) {
  const data = { ...initial }
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => {
      data[k] = String(v)
    },
    data,
  }
}

const brokenStorage = {
  getItem() {
    throw new Error('SecurityError')
  },
  setItem() {
    throw new Error('SecurityError')
  },
}

describe('resolveInitialLocale (RF-60 a RF-62)', () => {
  it.each([
    [['fr', 'en'], 'en'],
    [['es-MX'], 'es'],
    [['en-GB'], 'en'],
    [['de'], 'es'],
    [[], 'es'],
    [undefined, 'es'],
    [['EN-us', 'es'], 'en'],
  ])('%j → %s', (languages, expected) => {
    expect(resolveInitialLocale(languages)).toBe(expected)
  })
})

describe('localeStorage (RF-65, RF-66, RF-69)', () => {
  it('guarda y lee un idioma válido', () => {
    const storage = memoryStorage()
    saveLocale('en', storage)
    expect(storage.data[LOCALE_STORAGE_KEY]).toBe('en')
    expect(readStoredLocale(storage)).toBe('en')
  })

  it('ignora un valor manipulado', () => {
    expect(readStoredLocale(memoryStorage({ [LOCALE_STORAGE_KEY]: 'xx' }))).toBeNull()
  })

  it('tolera un almacenamiento inaccesible', () => {
    expect(readStoredLocale(brokenStorage)).toBeNull()
    expect(() => saveLocale('es', brokenStorage)).not.toThrow()
  })
})

describe('getInitialLocale (RF-65, RF-67, RF-69)', () => {
  it('la elección guardada manda sobre el navegador', () => {
    const storage = memoryStorage({ [LOCALE_STORAGE_KEY]: 'en' })
    expect(getInitialLocale({ storage, browserLanguages: ['es'] })).toBe('en')
  })

  it('sin elección aplica la regla de primera visita', () => {
    expect(getInitialLocale({ storage: memoryStorage(), browserLanguages: ['fr', 'en'] })).toBe('en')
  })

  it('con elección manipulada aplica la regla de primera visita', () => {
    const storage = memoryStorage({ [LOCALE_STORAGE_KEY]: 'xx' })
    expect(getInitialLocale({ storage, browserLanguages: ['de'] })).toBe('es')
  })

  it('con almacenamiento inaccesible aplica la regla de primera visita', () => {
    expect(getInitialLocale({ storage: brokenStorage, browserLanguages: ['en-GB'] })).toBe('en')
  })
})
