import { act, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { WIDE_MEDIA_QUERY } from '../config/layoutConstants.js'
import { renderWithProviders } from '../test/renderWithProviders.jsx'
import { TeamCell } from './TeamCell.jsx'

/** Simula una ventana de `width` px: coincide la consulta de 1024 px o no. */
function mockWidth(width) {
  const listeners = new Set()
  const media = {
    get matches() {
      return width >= 1024
    },
    media: WIDE_MEDIA_QUERY,
    addEventListener: (_type, listener) => listeners.add(listener),
    removeEventListener: (_type, listener) => listeners.delete(listener),
  }
  vi.stubGlobal('matchMedia', vi.fn((query) => (query === WIDE_MEDIA_QUERY ? media : { matches: false, addEventListener() {}, removeEventListener() {} })))
  return {
    resize(next) {
      width = next
      act(() => listeners.forEach((listener) => listener({ matches: media.matches })))
    },
  }
}

const identity = {
  id: 'i1',
  shortName: 'Los Angeles Thieves',
  abbreviation: 'LAT',
  logoUrl: '/api/logos/abc',
  primaryColor: '#ff0000',
  secondaryColor: null,
  validFrom: '2021-12-15T00:00:00Z',
}

const cell = () => screen.getByTestId('team-cell')

describe('equipo en una tabla (spec 004, §2.2, RF-14 a RF-16, RF-18)', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('desde 1024 px: insignia y nombre corto', () => {
    mockWidth(1024)
    renderWithProviders(<TeamCell identity={identity} />)
    expect(cell()).toHaveTextContent('Los Angeles Thieves')
    expect(cell()).not.toHaveTextContent('LAT')
    expect(cell().querySelector('img')).toHaveAttribute('src', '/api/logos/abc')
  })

  it('por debajo de 1024 px: insignia y abreviatura, con el nombre corto para el lector', () => {
    mockWidth(1023)
    renderWithProviders(<TeamCell identity={identity} />)
    const visible = screen.getByText('LAT')
    expect(visible).toHaveAttribute('aria-hidden', 'true')
    expect(screen.getByText('Los Angeles Thieves')).toHaveClass('sr-only')
    expect(cell().querySelector('img')).toHaveAttribute('src', '/api/logos/abc')
  })

  it('cambia al cruzar los 1024 px sin recargar', () => {
    const window = mockWidth(1440)
    renderWithProviders(<TeamCell identity={identity} />)
    expect(screen.queryByText('LAT')).toBeNull()
    window.resize(800)
    expect(screen.getByText('LAT')).toBeInTheDocument()
    window.resize(1024)
    expect(screen.queryByText('LAT')).toBeNull()
  })

  it('el nombre accesible es siempre el nombre corto', () => {
    for (const width of [1023, 1024]) {
      mockWidth(width)
      const { unmount } = renderWithProviders(<TeamCell identity={identity} />)
      const readable = [...cell().querySelectorAll(':not([aria-hidden="true"])')]
        .filter((node) => node.children.length === 0 && node.tagName !== 'IMG')
        .map((node) => node.textContent)
        .join('')
      expect(readable).toBe('Los Angeles Thieves')
      // El logo es decorativo: el nombre ya lo dice.
      expect(cell().querySelector('img')).toHaveAttribute('alt', '')
      unmount()
    }
  })

  it('sin logo propio usa el de la identidad más reciente de la franquicia (RF-14 de la 002)', () => {
    mockWidth(1024)
    const old = { ...identity, id: 'i0', logoUrl: null }
    const latest = { ...identity, id: 'i2', logoUrl: '/api/logos/new', validFrom: '2026-09-24T00:00:00Z' }
    renderWithProviders(<TeamCell identity={old} identities={[old, latest]} />)
    expect(cell().querySelector('img')).toHaveAttribute('src', '/api/logos/new')
  })

  it('sin ningún logo: la abreviatura sobre su color primario, oculta al lector', () => {
    mockWidth(1024)
    renderWithProviders(<TeamCell identity={{ ...identity, logoUrl: null }} />)
    expect(cell().querySelector('img')).toBeNull()
    const badge = screen.getByTestId('team-badge')
    expect(badge).toHaveTextContent('LAT')
    expect(badge).toHaveAttribute('aria-hidden', 'true')
    expect(badge).toHaveStyle({ backgroundColor: '#ff0000' })
  })

  it('el nombre es texto, sin enlace (RF-18)', () => {
    mockWidth(1024)
    renderWithProviders(<TeamCell identity={identity} />)
    expect(screen.queryByRole('link')).toBeNull()
  })
})
