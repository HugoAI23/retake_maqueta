import { expect, test } from '@playwright/test'
import { expectNoA11yViolations, expectNoHorizontalScroll, mockSeason, setBrowserLanguages } from './helpers.js'

/**
 * Sección Posiciones de extremo a extremo (spec 004, T-029): API simulada en el navegador, con
 * datos [FICTICIO]. Criterios 4 a 8 de la spec.
 */

const LONG_NAME = '[FICTICIO] Equipo con un nombre larguísimo que no cabe'

function row(i, fields = {}) {
  return {
    franchiseId: `f${i}`,
    identity: {
      id: `i${i}`,
      shortName: `[FICTICIO] Equipo ${i}`,
      abbreviation: `E${String(i).padStart(2, '0')}`,
      logoUrl: null,
      primaryColor: '#335577',
      secondaryColor: null,
      validFrom: '2021-12-15T00:00:00Z',
      changedAt: null,
    },
    position: i,
    points: 300 - i * 20,
    series: { won: 14 - i, lost: i },
    maps: { won: 40 - i * 2, lost: 10 + i * 2 },
    changedAt: '2026-06-01T10:00:00Z',
    ...fields,
  }
}

const STANDINGS = Array.from({ length: 14 }, (_, index) => row(index + 1))
STANDINGS[2] = { ...STANDINGS[2], identity: { ...STANDINGS[2].identity, shortName: LONG_NAME } }
// Posición compartida (RF-48).
STANDINGS[13] = { ...STANDINGS[13], position: 13 }

async function mockStandings(page, standings = STANDINGS) {
  await mockSeason(page, 2026)
  await page.route('**/api/standings', (route) => route.fulfill({ json: standings }))
  await page.route('**/api/franchises', (route) => route.fulfill({ json: [] }))
  await page.route('**/api/freshness', (route) =>
    route.fulfill({
      json: {
        standings: { lastChangedAt: '2026-06-01T09:00:00Z', stale: false },
        matches: { lastChangedAt: '2026-06-01T09:00:00Z', stale: false },
      },
    }))
}

const table = (page) => page.getByRole('table', { name: /Tabla de posiciones|Standings/ })
const rowHeaders = (page) => table(page).getByRole('rowheader')

/** Espera a que la entrada de la tabla termine: ninguna fila con estilos de la entrada. */
async function waitForEntrance(page) {
  await expect(table(page)).toBeVisible()
  await page.waitForFunction(() =>
    [...document.querySelectorAll('tbody tr')].every((tr) => !tr.style.opacity && !tr.style.transform))
}

test.describe('Posiciones: anchos y columnas fijas (RF-12 a RF-16, RF-50; criterio 4)', () => {
  for (const width of [320, 1023, 1024, 1440]) {
    test(`a ${width} px: sin scroll horizontal de la página y con la tabla completa`, async ({ page }) => {
      await mockStandings(page)
      await page.setViewportSize({ width, height: 900 })
      await page.goto('/standings')
      await waitForEntrance(page)
      await expectNoHorizontalScroll(page)
      await expect(rowHeaders(page)).toHaveCount(14)
      // Nombre corto desde 1024 px; abreviatura por debajo (RF-14, RF-15).
      const first = rowHeaders(page).first()
      if (width >= 1024) await expect(first).toContainText('[FICTICIO] Equipo 1')
      else await expect(first.locator('[aria-hidden="true"]').last()).toHaveText('E01')
      // El nombre legible es siempre el nombre corto (RF-16).
      await expect(table(page).getByRole('rowheader', { name: /\[FICTICIO\] Equipo 1$/ })).toHaveCount(1)
    })
  }

  test('a 320 px la tabla se desplaza en su caja y Pos. y Equipo quedan fijas', async ({ page }) => {
    await mockStandings(page)
    await page.setViewportSize({ width: 320, height: 900 })
    await page.goto('/standings')
    await waitForEntrance(page)
    const box = table(page).locator('..')
    const before = await page.evaluate(() => {
      const cells = document.querySelector('tbody tr').cells
      return [cells[0].getBoundingClientRect().left, cells[1].getBoundingClientRect().left, cells[2].getBoundingClientRect().left]
    })
    await box.evaluate((node) => {
      node.scrollLeft = node.scrollWidth
    })
    const after = await page.evaluate(() => {
      const cells = document.querySelector('tbody tr').cells
      return [cells[0].getBoundingClientRect().left, cells[1].getBoundingClientRect().left, cells[2].getBoundingClientRect().left]
    })
    expect(after[0]).toBeCloseTo(before[0], 0)
    expect(after[1]).toBeCloseTo(before[1], 0)
    expect(after[2]).toBeLessThan(before[2])
    await expectNoHorizontalScroll(page)
  })
})

test.describe('Posiciones: orden (RF-3 a RF-6, RF-10, RF-11, RF-11a, RF-37)', () => {
  test('se ordena solo con el teclado y la cabecera se llama como su columna', async ({ page }) => {
    await mockStandings(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/standings')
    await waitForEntrance(page)
    // El nombre accesible sale del contenido, no del `title` "Ordenar por…".
    const points = table(page).getByRole('button', { name: 'Puntos', exact: true })
    await points.focus()
    await page.keyboard.press('Enter')
    await expect(table(page).getByRole('columnheader', { name: /Puntos/ })).toHaveAttribute('aria-sort', 'descending')
    // Chrome separa con un espacio el texto para el lector: "Puntos , ordenada de mejor a peor".
    await expect(table(page).getByRole('button', { name: /^Puntos\s?, ordenada de mejor a peor$/ })).toBeFocused()
    await page.keyboard.press('Space')
    await expect(table(page).getByRole('columnheader', { name: /Puntos/ })).toHaveAttribute('aria-sort', 'ascending')
    await expect(rowHeaders(page).first()).toContainText('[FICTICIO] Equipo 14')
    await page.keyboard.press('Enter')
    await expect(table(page).locator('th[aria-sort]')).toHaveCount(0)
    await expect(rowHeaders(page).first()).toContainText('[FICTICIO] Equipo 1')
  })

  test('Atrás y Adelante recuperan el orden; entrar desde el menú y recargar, no', async ({ page }) => {
    await mockStandings(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/standings')
    await waitForEntrance(page)
    await table(page).getByRole('button', { name: 'Series', exact: true }).click()
    await table(page).getByRole('button', { name: /^Series/ }).click()
    const sorted = table(page).locator('th[aria-sort]')
    await expect(sorted).toHaveAttribute('aria-sort', 'ascending')

    await page.locator('header').getByRole('link', { name: 'Partidos' }).click()
    await expect(page).toHaveURL('/matches')
    await page.goBack()
    await waitForEntrance(page)
    await expect(sorted).toHaveAttribute('aria-sort', 'ascending')
    await page.goForward()
    await page.goBack()
    await waitForEntrance(page)
    await expect(sorted).toHaveAttribute('aria-sort', 'ascending')

    await page.reload()
    await waitForEntrance(page)
    await expect(sorted).toHaveCount(0)

    await table(page).getByRole('button', { name: 'Puntos', exact: true }).click()
    await page.locator('header').getByRole('link', { name: 'Partidos' }).click()
    await page.locator('header').getByRole('link', { name: 'Posiciones' }).click()
    await waitForEntrance(page)
    await expect(sorted).toHaveCount(0)
  })
})

test.describe('Posiciones: nombre recortado (RF-17 a RF-17b)', () => {
  test('se consulta con un toque, con el foco o el puntero, y Escape lo cierra', async ({ page }) => {
    await mockStandings(page)
    await page.setViewportSize({ width: 1024, height: 900 })
    await page.goto('/standings')
    await waitForEntrance(page)
    const name = table(page).locator('[data-truncated-name]', { hasText: LONG_NAME })
    await expect(name).toHaveAttribute('tabindex', '0')

    await name.click()
    const tooltip = page.getByRole('tooltip')
    await expect(tooltip).toHaveText(LONG_NAME)
    await expect(name).toHaveAttribute('aria-describedby', await tooltip.getAttribute('id'))
    // Dentro de la ventana.
    const bubble = await tooltip.boundingBox()
    expect(bubble.x).toBeGreaterThanOrEqual(0)
    expect(bubble.x + bubble.width).toBeLessThanOrEqual(1024)
    // Se puede pasar el puntero a la burbuja sin que desaparezca.
    await tooltip.hover()
    await expect(tooltip).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(tooltip).toHaveCount(0)
    await expect(name).toBeFocused()

    // Los nombres que caben no reciben el foco.
    await expect(table(page).locator('[data-truncated-name]', { hasText: '[FICTICIO] Equipo 1' }).first()).not.toHaveAttribute('tabindex')
  })
})

test.describe('Posiciones: animaciones (RF-28 a RF-29, RF-33, RF-34)', () => {
  test('la entrada termina en menos de 800 ms desde que empieza (con la transición, ~1 s)', async ({ page }) => {
    await mockStandings(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/')
    await page.locator('header').getByRole('link', { name: 'Posiciones' }).click()
    await expect(table(page)).toBeVisible()
    const start = Date.now()
    await waitForEntrance(page)
    // Transición de página (200 ms) + entrada (≤ 800 ms), con margen para el propio navegador.
    expect(Date.now() - start).toBeLessThan(1400)
    // Las cifras terminan en su valor.
    const points = page.locator('tbody tr').first().locator('td').nth(1)
    await expect(points.locator('[aria-hidden="true"]')).toHaveText('280')
  })

  test('con reducir movimiento, la tabla aparece sin ninguna animación', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await mockStandings(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/standings')
    await expect(table(page)).toBeVisible()
    const state = await page.evaluate(() => {
      const first = document.querySelector('tbody tr')
      return { opacity: first.style.opacity, transform: first.style.transform, points: first.cells[2].textContent }
    })
    expect(state).toEqual({ opacity: '', transform: '', points: '280280' })
  })
})

test.describe('Posiciones: zoom, idiomas y auditoría (RF-35, RF-39, RF-40, RF-48; criterios 5 a 8)', () => {
  test('una ventana de 1280 px al 200 % (640 px): sin scroll de la página y se puede ordenar', async ({ page }) => {
    await mockStandings(page)
    await page.setViewportSize({ width: 640, height: 400 })
    await page.goto('/standings')
    await waitForEntrance(page)
    await expectNoHorizontalScroll(page)
    await table(page).getByRole('button', { name: 'Mapas', exact: true }).click()
    await expect(table(page).locator('th[aria-sort]')).toHaveCount(1)
  })

  test('en inglés: títulos, cabeceras y posición compartida', async ({ page }) => {
    await setBrowserLanguages(page, ['en'])
    await mockStandings(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/standings')
    await expect(page.getByRole('heading', { level: 1, name: 'Standings' })).toBeVisible()
    await expect(page.getByText('2026 Season', { exact: true })).toBeVisible()
    await expect(page).toHaveTitle('Standings · Retake')
    for (const header of ['Pos.', 'Team', 'Points', 'Series', 'Maps', '±Maps']) {
      await expect(table(page).getByRole('button', { name: header, exact: true })).toBeVisible()
    }
    await expect(page.locator('tbody .sr-only', { hasText: '13, tied' })).toHaveCount(2)
  })

  for (const lang of ['es', 'en']) {
    for (const width of [320, 1440]) {
      test(`${lang} a ${width} px: sin incumplimientos de axe, también ordenada y con la burbuja abierta`, async ({ page }) => {
        await setBrowserLanguages(page, [lang])
        await mockStandings(page)
        await page.setViewportSize({ width, height: 900 })
        await page.goto('/standings')
        await waitForEntrance(page)
        await expectNoA11yViolations(page)
        await table(page).locator('thead button').nth(2).click()
        await expectNoA11yViolations(page)
        if (width === 1440) {
          await page.setViewportSize({ width: 1024, height: 900 })
          await table(page).locator('[data-truncated-name]', { hasText: LONG_NAME }).focus()
          await expect(page.getByRole('tooltip')).toBeVisible()
          await expectNoA11yViolations(page)
        }
      })
    }
  }
})
