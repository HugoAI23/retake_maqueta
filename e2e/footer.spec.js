import { expect, test } from '@playwright/test'
import { mockSeason } from './helpers.js'

// Spec 003: año de la temporada desde la API (RF-74 a RF-78) y atribución de las fuentes (RF-160).
test.describe('pie de página de la spec 003', () => {
  for (const path of ['/', '/matches', '/no-existe', '/admin']) {
    test(`año y atribución en ${path}`, async ({ page }) => {
      await mockSeason(page, 2026)
      await page.route('**/api/admin/me', (route) => route.fulfill({ status: 401, json: { detail: 'x' } }))
      await page.goto(path)
      const footer = page.getByRole('contentinfo')
      await expect(footer).toContainText('Temporada 2026')
      for (const href of ['https://www.breakingpoint.gg', 'https://cod-esports.fandom.com',
        'https://www.callofdutyleague.com', 'https://creativecommons.org/licenses/by-sa/3.0/']) {
        await expect(footer.locator(`a[href="${href}"]`)).toHaveCount(1)
      }
    })
  }

  test('sin año mientras la API no lo da', async ({ page }) => {
    await page.route('**/api/season/current', (route) => route.fulfill({ status: 404, json: { detail: 'x' } }))
    await page.goto('/')
    await expect(page.getByRole('contentinfo')).not.toContainText(/Temporada \d{4}/)
  })
})
