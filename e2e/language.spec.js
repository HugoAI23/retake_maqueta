import { expect, test } from '@playwright/test'
import { menuButton, mockSeason, setBrowserLanguages } from './helpers.js'

test.describe('idioma (RF-59 a RF-69)', () => {
  test('primera visita: primer idioma admitido de la lista del navegador', async ({ page }) => {
    await setBrowserLanguages(page, ['fr-FR', 'en-GB', 'es'])
    await mockSeason(page, 2026) // spec 003 (T-080): el año sale de la API
    await page.goto('/')
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    await expect(page.getByRole('contentinfo')).toContainText('2026 season')
  })

  test('primera visita con un idioma no admitido: español', async ({ page }) => {
    await setBrowserLanguages(page, ['de-DE'])
    await page.goto('/')
    await expect(page.locator('html')).toHaveAttribute('lang', 'es')
  })

  test('variante regional del español: es-MX → español', async ({ page }) => {
    await setBrowserLanguages(page, ['es-MX'])
    await page.goto('/')
    await expect(page.locator('html')).toHaveAttribute('lang', 'es')
  })

  test('cambiar de idioma conserva la página y el scroll, y se recuerda al recargar', async ({ page }) => {
    await setBrowserLanguages(page, ['es'])
    await page.setViewportSize({ width: 1440, height: 400 })
    await page.goto('/players')
    await page.evaluate(() => window.scrollTo(0, 200))
    const before = await page.evaluate(() => window.scrollY)
    expect(before).toBeGreaterThan(0)
    // Spec 003 (I-30 de su plan): con la atribución de las fuentes el pie es más alto, y el botón de
    // idioma queda medio oculto con este scroll; `click` haría que Playwright desplazara la página
    // para mostrarlo. `dispatchEvent` pulsa el botón sin mover nada, que es lo que se comprueba aquí.
    await page.locator('header').getByRole('button', { name: 'English' }).dispatchEvent('click')
    await expect(page.getByRole('main').getByRole('heading', { name: 'Players' })).toBeAttached()
    await expect(page).toHaveURL('/players')
    expect(await page.evaluate(() => window.scrollY)).toBe(before)
    await page.reload()
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  })

  test('la elección de Retake manda sobre el navegador', async ({ page }) => {
    await setBrowserLanguages(page, ['es'])
    await page.addInitScript(() => localStorage.setItem('retake.locale', 'en'))
    await page.goto('/')
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  })

  test('un valor guardado manipulado aplica la regla de primera visita', async ({ page }) => {
    await setBrowserLanguages(page, ['en'])
    await page.addInitScript(() => localStorage.setItem('retake.locale', 'xx'))
    await page.goto('/')
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  })

  test('cambiar de idioma con el panel abierto lo mantiene abierto', async ({ page }) => {
    await setBrowserLanguages(page, ['es'])
    await page.setViewportSize({ width: 375, height: 740 })
    await page.goto('/')
    await menuButton(page).click()
    await page.getByRole('dialog').getByRole('button', { name: 'English' }).click()
    await expect(page.getByRole('dialog', { name: 'Sections menu' })).toBeVisible()
  })

  test('cada pestaña conserva su idioma hasta recargarla (RF-68)', async ({ context }) => {
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'languages', { get: () => ['es'] })
    })
    await context.clearCookies()
    const first = await context.newPage()
    await first.setViewportSize({ width: 1440, height: 800 })
    await first.goto('/')
    await expect(first.locator('html')).toHaveAttribute('lang', 'es')

    const second = await context.newPage()
    await second.setViewportSize({ width: 1440, height: 800 })
    await second.goto('/')
    await second.locator('header').getByRole('button', { name: 'English' }).click()
    await expect(second.locator('html')).toHaveAttribute('lang', 'en')

    // La primera pestaña no cambia...
    await first.waitForTimeout(300)
    await expect(first.locator('html')).toHaveAttribute('lang', 'es')
    // ...hasta que se recarga.
    await first.reload()
    await expect(first.locator('html')).toHaveAttribute('lang', 'en')
  })
})
