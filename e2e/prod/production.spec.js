import { expect, test } from '@playwright/test'
import { mainNav } from '../helpers.js'

// Solo contra la versión de producción (npm run build + preview).
test.describe('versión de producción (RF-94, RF-95, plan §5)', () => {
  test('/dev/block-demo muestra "Página no encontrada"', async ({ page }) => {
    await page.goto('/dev/block-demo')
    await expect(page.getByRole('heading', { name: 'Página no encontrada' })).toBeVisible()
    await expect(mainNav(page).locator('[aria-current="page"]')).toHaveCount(0)
  })

  test('el paquete no contiene código ni textos de la demostración', async ({ page, request }) => {
    await page.goto('/')
    const scripts = await page.locator('script[src]').evaluateAll((els) => els.map((el) => el.src))
    expect(scripts.length).toBeGreaterThan(0)
    for (const src of scripts) {
      const body = await (await request.get(src)).text()
      for (const needle of ['block-demo', 'BlockDemoPage', 'Demostración de bloque', 'demoScenarios', 'FaZe VGS']) {
        expect(body, `${src} no contiene "${needle}"`).not.toContain(needle)
      }
    }
  })
})
