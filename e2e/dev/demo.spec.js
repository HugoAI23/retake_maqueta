import { expect, test } from '@playwright/test'
import { expectNoA11yViolations, mainNav } from '../helpers.js'

// Solo en desarrollo: la página de demostración no existe en producción.
test.describe('bloque de demostración (RF-40 a RF-53, RF-72, RF-89 a RF-94)', () => {
  test.beforeEach(async ({ page }) => {
    await page.clock.install()
    await page.setViewportSize({ width: 1280, height: 900 })
    await page.goto('/dev/block-demo')
    await expect(page.getByRole('heading', { name: 'Demostración de bloque' })).toBeVisible()
  })

  const block = (page) => page.getByTestId('demo-block')
  const count = (page) => page.getByTestId('demo-load-count')
  const choose = (page, name) => page.getByRole('radio', { name }).check()

  test('no tiene entrada en el menú (RF-94)', async ({ page }) => {
    await expect(mainNav(page).getByRole('link')).toHaveCount(8)
    await expect(page.locator('a[href="/dev/block-demo"]')).toHaveCount(0)
  })

  test('ok: esqueleto y después contenido, sin avisos (RF-40, RF-47)', async ({ page }) => {
    await expect(block(page).getByRole('status')).toBeVisible()
    await page.clock.fastForward(1000)
    await expect(block(page)).toContainText('FaZe VGS')
    await expect(block(page).getByRole('alert')).toHaveCount(0)
  })

  test('fail: aviso y "Reintentar"; varias pulsaciones, un solo intento (RF-41, RF-44 a RF-46)', async ({ page }) => {
    await choose(page, /Fallo de carga/)
    await page.clock.fastForward(1000)
    const retry = block(page).getByRole('button', { name: 'Reintentar: Bloque de demostración' })
    await expect(retry).toBeVisible()
    await expect(count(page)).toContainText('1')
    await retry.dblclick()
    await expect(count(page)).toContainText('2')
    await page.clock.fastForward(1000)
    await expect(retry).toBeVisible()
    await retry.click()
    await expect(count(page)).toContainText('3')
  })

  test('hang: error a los 15 s (RF-42)', async ({ page }) => {
    await choose(page, /no termina/)
    await page.clock.fastForward(14000)
    await expect(block(page).getByRole('status')).toBeVisible()
    await page.clock.fastForward(1000)
    await expect(block(page).getByRole('alert')).toBeVisible()
  })

  test('late: error a los 15 s y los datos sustituyen al aviso a los 20 s (RF-43, RF-93)', async ({ page }) => {
    await choose(page, /Datos tardíos/)
    await page.clock.fastForward(15000)
    await expect(block(page).getByRole('alert')).toBeVisible()
    await page.clock.fastForward(5000)
    await expect(block(page)).toContainText('FaZe VGS')
    await expect(block(page).getByRole('alert')).toHaveCount(0)
  })

  test('un bloque en error no bloquea el menú (RF-48)', async ({ page }) => {
    await choose(page, /Fallo de carga/)
    await page.clock.fastForward(1000)
    await expect(block(page).getByRole('alert')).toBeVisible()
    await mainNav(page).getByRole('link', { name: 'Equipos' }).click()
    await expect(page).toHaveURL('/teams')
  })

  test('al redimensionar se conserva el estado (RF-49)', async ({ page }) => {
    await choose(page, /Fallo de carga/)
    await page.clock.fastForward(1000)
    await expect(block(page).getByRole('alert')).toBeVisible()
    await page.setViewportSize({ width: 375, height: 800 })
    await expect(block(page).getByRole('alert')).toBeVisible()
    await expect(count(page)).toContainText('1')
  })

  test('sin conexión: aviso, contenido conservado y reintento automático al volver (RF-50 a RF-53)', async ({ page, context }) => {
    // Contenido cargado: se conserva sin red.
    await page.clock.fastForward(1000)
    await expect(block(page)).toContainText('FaZe VGS')
    await context.setOffline(true)
    await expect(page.getByTestId('offline-banner')).toContainText('Sin conexión')
    await expect(block(page)).toContainText('FaZe VGS')

    // Bloque en error: reintenta solo al volver la red.
    await choose(page, /Fallo de carga/)
    await page.clock.fastForward(1000)
    await expect(block(page).getByRole('alert')).toBeVisible()
    await expect(count(page)).toContainText('1')
    await context.setOffline(false)
    await expect(page.getByTestId('offline-banner')).not.toContainText('Sin conexión')
    await expect(count(page)).toContainText('2')
  })

  test('los nombres propios no se traducen (RF-72)', async ({ page }) => {
    await page.clock.fastForward(1000)
    await expect(block(page)).toContainText('FaZe VGS vs OpTic Texas')
    await page.locator('header').getByRole('button', { name: 'English' }).click()
    await expect(block(page)).toContainText('Sample match')
    await expect(block(page)).toContainText('FaZe VGS vs OpTic Texas')
    await expect(block(page)).toContainText('Hardpoint')
  })

  test('accesible en sus tres estados (RF-73)', async ({ page }) => {
    await expectNoA11yViolations(page)
    await choose(page, /Fallo de carga/)
    await page.clock.fastForward(1000)
    await expect(block(page).getByRole('alert')).toBeVisible()
    await expectNoA11yViolations(page)
    await choose(page, /Carga correcta/)
    await page.clock.fastForward(1000)
    await expect(block(page)).toContainText('FaZe VGS')
    await expectNoA11yViolations(page)
  })
})
