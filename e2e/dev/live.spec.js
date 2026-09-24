import { expect, test } from '@playwright/test'
import { expectNoA11yViolations } from '../helpers.js'

// Solo en desarrollo: el bloque en vivo vive en la página de demostración (spec 003, T-074, T-082).
const identity = (shortName) => ({ id: shortName, shortName, abbreviation: null, logoUrl: null, primaryColor: null,
  secondaryColor: null, validFrom: '2025-01-01T00:00:00Z', changedAt: null })
const liveMatch = {
  id: 'm1', eventId: 'e', eventName: '[FICTICIO] Major', phase: null, bestOf: 5, status: 'live',
  scheduledAt: '2026-12-05T20:00:00Z', scheduleHistory: [], winnerSide: null, correctedFields: [], maps: [],
  slots: [{ franchiseId: 'a', identity: identity('[FICTICIO] Uno'), origin: null },
    { franchiseId: 'b', identity: identity('[FICTICIO] Dos'), origin: null }],
  mapsWon: [1, 0], liveMap: { mode: 'Hardpoint', score: [120, 90] }, changedAt: '2026-12-05T20:01:00Z', isStale: false,
}

test.describe('bloque en vivo de la demostración (RF-79 a RF-96, RF-155 a RF-159)', () => {
  test('partido en vivo con su hora y el aviso de datos sin actualizar', async ({ page }) => {
    await page.route('**/api/matches', (route) => route.fulfill({ json: [liveMatch] }))
    await page.route('**/api/freshness', (route) =>
      route.fulfill({ json: { live: { lastChangedAt: '2026-12-05T20:01:00Z', stale: true } } }))
    await page.goto('/dev/block-demo')
    const block = page.getByTestId('live-demo')
    await expect(block).toContainText('[FICTICIO] Uno 1 - 0 [FICTICIO] Dos')
    await expect(block).toContainText('Actualizado:')
    await expect(block).toContainText('Estos datos pueden no estar al día.')
    await expectNoA11yViolations(page)
  })

  test('el canal de eventos llega a través del proxy de Vite con su latido (T-061)', async ({ page }) => {
    test.setTimeout(40_000)
    await page.goto('/dev/block-demo')
    const beat = await page.evaluate(() => new Promise((resolve, reject) => {
      const source = new EventSource('/api/stream')
      const timer = setTimeout(() => reject(new Error('sin latido en 25 s')), 25_000)
      source.addEventListener('heartbeat', (event) => {
        clearTimeout(timer)
        source.close()
        resolve(JSON.parse(event.data))
      })
    }))
    expect(beat.now).toMatch(/^\d{4}-\d{2}-\d{2}T/)
  })
})
