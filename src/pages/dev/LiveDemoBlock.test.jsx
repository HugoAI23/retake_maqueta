import { act, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../../test/renderWithProviders.jsx'
import { LiveAnnouncerProvider } from '../../live/LiveAnnouncer.jsx'
import { LiveProvider } from '../../live/LiveProvider.jsx'
import { LiveDemoBlock } from './LiveDemoBlock.jsx'

const identity = (shortName) => ({ id: shortName, shortName, abbreviation: null, logoUrl: null, primaryColor: null,
                                   secondaryColor: null, validFrom: '2025-01-01T00:00:00Z', changedAt: null })
const match = (score, changedAt, isStale = false) => ({
  id: 'm1', eventId: 'e', eventName: '[FICTICIO] Major', phase: null, bestOf: 5, status: 'live',
  scheduledAt: '2026-12-05T20:00:00Z', scheduleHistory: [], winnerSide: null, correctedFields: [], maps: [],
  slots: [{ franchiseId: 'a', identity: identity('[FICTICIO] Uno'), origin: null },
          { franchiseId: 'b', identity: identity('[FICTICIO] Dos'), origin: null }],
  mapsWon: score, liveMap: { mode: 'Hardpoint', score: [120, 90] }, changedAt, isStale,
})

function fakeChannel() {
  const listeners = new Set()
  return { subscribe: (fn) => (listeners.add(fn), () => listeners.delete(fn)), getStatus: () => ({ cutSince: null }),
           close: () => {}, emit: (event) => listeners.forEach((fn) => fn(event)) }
}

function setup(loadMatches, freshness = {}) {
  const channel = fakeChannel()
  renderWithProviders(
    <LiveProvider channel={channel} loadFreshness={() => Promise.resolve(freshness)}>
      <LiveAnnouncerProvider>
        <LiveDemoBlock loadMatches={loadMatches} />
      </LiveAnnouncerProvider>
    </LiveProvider>,
  )
  return channel
}

describe('bloque de demostración en vivo (T-074; RF-79 a RF-96, RF-155 a RF-159)', () => {
  it('muestra los partidos en vivo con su hora de última actualización', async () => {
    setup(() => Promise.resolve([match([1, 0], '2026-12-05T20:01:00Z')]))
    const block = await screen.findByTestId('live-demo')
    expect(await within(block).findByText(/\[FICTICIO\] Uno 1 - 0 \[FICTICIO\] Dos/)).toBeInTheDocument()
    expect(within(block).getByText(/^Actualizado: /)).toBeInTheDocument()
  })

  it('sin partidos en vivo, dice que no hay ninguno y la hora es la del último cambio vigilado', async () => {
    setup(() => Promise.resolve([]), { live: { lastChangedAt: '2026-12-05T19:00:00Z', stale: false } })
    expect(await screen.findByText('No hay ningún partido en vivo.')).toBeInTheDocument()
    expect(await screen.findByText(/^Actualizado: /)).toBeInTheDocument()
  })

  it('muestra el aviso de datos sin actualizar sin retirar el contenido', async () => {
    setup(() => Promise.resolve([match([1, 0], '2026-12-05T20:01:00Z', true)]))
    expect(await screen.findByText('Estos datos pueden no estar al día.')).toBeInTheDocument()
    expect(screen.getByText(/1 - 0/)).toBeInTheDocument()
  })

  it('anuncia el cambio de marcador en vivo sin interrumpir', async () => {
    let score = [1, 0]
    const channel = setup(() => Promise.resolve([match(score, '2026-12-05T20:01:00Z')]))
    await screen.findByText(/1 - 0/)
    score = [2, 0]
    await act(async () => channel.emit({ type: 'change', datasets: ['live'], changedAt: 'x' }))
    expect(await screen.findByRole('status')).toHaveTextContent('[FICTICIO] Uno 2 - 0 [FICTICIO] Dos')
  })
})
