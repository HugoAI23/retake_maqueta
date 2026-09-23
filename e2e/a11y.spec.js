import { expect, test } from '@playwright/test'
import {
  expectNoA11yViolations,
  expectNoHorizontalScroll,
  mainNav,
  menuButton,
  SECTION_PATHS,
  setBrowserLanguages,
} from './helpers.js'

test.describe('auditoría WCAG 2.2 AA (RF-73, RF-74)', () => {
  for (const lang of ['es', 'en']) {
    for (const width of [320, 1440]) {
      test(`${lang} a ${width} px: todas las rutas sin incumplimientos`, async ({ page }) => {
        await setBrowserLanguages(page, [lang])
        await page.setViewportSize({ width, height: 800 })
        for (const path of [...SECTION_PATHS, '/no-existe']) {
          await page.goto(path)
          await page.getByRole('main').waitFor()
          await expectNoA11yViolations(page)
        }
      })
    }

    test(`${lang} a 320 px con el panel abierto`, async ({ page }) => {
      await setBrowserLanguages(page, [lang])
      await page.setViewportSize({ width: 320, height: 700 })
      await page.goto('/players')
      await menuButton(page).click()
      await expect(page.getByRole('dialog')).toBeVisible()
      await page.waitForTimeout(400)
      await expectNoA11yViolations(page)
    })
  }
})

test.describe('teclado (RF-76, RF-78 a RF-80)', () => {
  test('Tab recorre saltar-al-contenido, logo, entradas e idioma; Enter navega', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 800 })
    await page.goto('/')
    const reached = []
    for (let i = 0; i < 12; i += 1) {
      await page.keyboard.press('Tab')
      reached.push(
        await page.evaluate(() => {
          const el = document.activeElement
          const outline = getComputedStyle(el).outlineStyle
          return `${el.getAttribute('aria-label') ?? el.textContent.trim()}|${outline}`
        }),
      )
    }
    const names = reached.map((r) => r.split('|')[0])
    expect(names.slice(0, 12)).toEqual([
      'Saltar al contenido',
      'Retake, ir a Inicio',
      'Inicio',
      'Partidos',
      'Equipos',
      'Jugadores',
      'Torneos',
      'Posiciones',
      'Noticias',
      'Modelos de MLIA',
      'Español',
      'English',
    ])
    // Indicador de foco visible en cada elemento (RF-76).
    expect(reached.every((r) => r.split('|')[1] !== 'none')).toBe(true)

    // Enter sobre "Jugadores" navega.
    await page.goto('/')
    await mainNav(page).getByRole('link', { name: 'Jugadores' }).focus()
    await page.keyboard.press('Enter')
    await expect(page).toHaveURL('/players')
  })

  test('en móvil el botón de menú se abre con el teclado y el foco vuelve al cerrarlo', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 740 })
    await page.goto('/')
    await menuButton(page).focus()
    await page.keyboard.press('Enter')
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Cerrar menú' }).last()).toBeFocused()
    await page.keyboard.press('Escape')
    await expect(menuButton(page)).toBeFocused()
  })
})

test.describe('zoom al 200 % (RF-81)', () => {
  test('una ventana de 1280 px al 200 % equivale a 640 px: todo visible y usable', async ({ page }) => {
    await page.setViewportSize({ width: 640, height: 400 })
    for (const path of ['/', '/players', '/no-existe']) {
      await page.goto(path)
      await expectNoHorizontalScroll(page)
    }
    await menuButton(page).click()
    await page.getByRole('dialog').getByRole('link', { name: 'Posiciones' }).click()
    await expect(page).toHaveURL('/standings')
  })
})

test.describe('movimiento (RF-84 a RF-88)', () => {
  test('sin preferencia: el panel entra deslizándose', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 740 })
    await page.goto('/')
    await menuButton(page).click()
    const panel = page.locator('#mobile-nav-panel')
    await expect(panel).toHaveAttribute('style', /translateX/)
  })

  test('con reducir movimiento: el panel aparece sin deslizamiento y el cambio de página es inmediato', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.setViewportSize({ width: 375, height: 740 })
    await page.goto('/')
    await menuButton(page).click()
    const panel = page.locator('#mobile-nav-panel')
    await expect(panel).toBeVisible()
    expect(await panel.getAttribute('style')).toBeNull()
    await panel.getByRole('link', { name: 'Equipos' }).click()
    expect(await page.getByTestId('page-transition').getAttribute('style')).toBeNull()
  })
})
