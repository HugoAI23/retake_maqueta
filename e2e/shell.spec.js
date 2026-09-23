import { expect, test } from '@playwright/test'
import { expectNoHorizontalScroll, mainNav, menuButton, SECTION_PATHS, setBrowserLanguages, WIDTHS } from './helpers.js'

test.describe('marco y direcciones (RF-1, RF-2, RF-26, RF-27, RF-54)', () => {
  for (const path of [...SECTION_PATHS, '/no-existe']) {
    test(`${path} tiene el marco completo al abrir directamente y al recargar`, async ({ page }) => {
      for (const action of ['open', 'reload']) {
        if (action === 'open') await page.goto(path)
        else await page.reload()
        const ticker = page.getByTestId('score-ticker')
        const header = page.locator('header')
        await expect(ticker).toBeVisible()
        await expect(header).toBeVisible()
        await expect(page.getByRole('main')).toBeVisible()
        await expect(page.getByRole('contentinfo')).toBeVisible()
        const tickerBox = await ticker.boundingBox()
        const headerBox = await header.boundingBox()
        expect(tickerBox.y + tickerBox.height).toBeLessThanOrEqual(headerBox.y + 1)
        expect(tickerBox.width).toBe(page.viewportSize().width)
      }
    })
  }

  test('una dirección inventada muestra "Página no encontrada"', async ({ page }) => {
    await page.goto('/esto/no/existe')
    await expect(page.getByRole('heading', { name: 'Página no encontrada' })).toBeVisible()
    await page.getByRole('link', { name: 'Volver a Inicio' }).click()
    await expect(page).toHaveURL('/')
  })
})

test.describe('cinta y menú no fijos (RF-3)', () => {
  test('al hacer scroll se desplazan con la página', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 400 })
    await page.goto('/')
    await page.mouse.wheel(0, 600)
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0)
    const box = await page.locator('header').boundingBox()
    expect(box.y + box.height).toBeLessThanOrEqual(0)
  })
})

test.describe('menú en fila (RF-6, RF-7, RF-14, RF-24)', () => {
  for (const [lang, names] of [
    ['es', ['Inicio', 'Partidos', 'Equipos', 'Jugadores', 'Torneos', 'Posiciones', 'Noticias', /^Modelos de ML\s*IA$/]],
    ['en', ['Home', 'Matches', 'Teams', 'Players', 'Tournaments', 'Standings', 'News', /^ML Models\s*AI$/]],
  ]) {
    for (const width of [1024, 1440]) {
      test(`${lang} a ${width} px: fila completa, en orden y sin desbordar`, async ({ page }) => {
        await setBrowserLanguages(page, [lang])
        await page.setViewportSize({ width, height: 800 })
        await page.goto('/')
        const links = mainNav(page).getByRole('link')
        await expect(links).toHaveText(names)
        const tops = await links.evaluateAll((els) => els.map((el) => Math.round(el.getBoundingClientRect().top)))
        expect(new Set(tops).size, 'una sola fila').toBe(1)
        await expect(page.locator('header').getByRole('group').first()).toBeVisible()
        await expect(menuButton(page)).toBeHidden()
        await expectNoHorizontalScroll(page)
      })
    }
  }

  test('navega y marca la entrada activa', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 800 })
    await page.goto('/')
    await mainNav(page).getByRole('link', { name: 'Jugadores' }).click()
    await expect(page).toHaveURL('/players')
    await expect(mainNav(page).getByRole('link', { name: 'Jugadores' })).toHaveAttribute('aria-current', 'page')
  })

  test('Atrás y Adelante del navegador cambian de página (RF-28)', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 800 })
    await page.goto('/')
    await mainNav(page).getByRole('link', { name: 'Equipos' }).click()
    await mainNav(page).getByRole('link', { name: 'Noticias' }).click()
    await page.goBack()
    await expect(page.getByRole('main').getByRole('heading', { name: 'Equipos' })).toBeVisible()
    await page.goForward()
    await expect(page.getByRole('main').getByRole('heading', { name: 'Noticias' })).toBeVisible()
  })
})

test.describe('menú plegado a 375 px (RF-16 a RF-23, RF-28, RF-29, RF-82, RF-83)', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 740 })
    await page.goto('/')
  })

  test('logo, Modelos de ML y botón visibles; la fila oculta', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Retake, ir a Inicio' })).toBeVisible()
    await expect(page.locator('header').getByRole('link', { name: /Modelos de ML/ })).toBeVisible()
    await expect(menuButton(page)).toBeVisible()
    await expect(mainNav(page)).toBeHidden()
  })

  test('abrir, navegar con una entrada y cerrar', async ({ page }) => {
    await menuButton(page).click()
    const panel = page.getByRole('dialog')
    await expect(panel.getByRole('link')).toHaveCount(8)
    await panel.getByRole('link', { name: 'Torneos' }).click()
    await expect(page).toHaveURL('/tournaments')
    await expect(page.getByRole('dialog')).toHaveCount(0)
    await expect(menuButton(page)).toBeFocused()
  })

  test('Escape y pulsar fuera cierran el panel', async ({ page }) => {
    await menuButton(page).click()
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).toHaveCount(0)
    await menuButton(page).click()
    await page.mouse.click(10, 400)
    await expect(page.getByRole('dialog')).toHaveCount(0)
  })

  test('pasar a 1024 px con el panel abierto lo cierra', async ({ page }) => {
    await menuButton(page).click()
    await expect(page.getByRole('dialog')).toBeVisible()
    await page.setViewportSize({ width: 1024, height: 740 })
    await expect(page.getByRole('dialog')).toHaveCount(0)
  })

  test('Atrás del navegador con el panel abierto lo cierra', async ({ page }) => {
    await page.goto('/teams')
    await menuButton(page).click()
    await page.goBack()
    await expect(page).toHaveURL('/')
    await expect(page.getByRole('dialog')).toHaveCount(0)
  })

  test('el fondo no se desplaza y Tab no sale del panel', async ({ page }) => {
    await menuButton(page).click()
    const panel = page.getByRole('dialog')
    await expect(panel).toBeVisible()
    expect(await page.evaluate(() => document.body.style.overflow)).toBe('hidden')
    for (let i = 0; i < 15; i += 1) {
      await page.keyboard.press('Tab')
      const inside = await page.evaluate(() => {
        const active = document.activeElement
        return active === document.body || document.getElementById('mobile-nav-panel').contains(active)
      })
      expect(inside, `Tab ${i + 1} sigue dentro del panel`).toBe(true)
    }
  })
})

// Mide los tres huecos en el mismo instante, tras cargar las fuentes,
// para que un reajuste de la página no mezcle medidas de momentos distintos.
async function measureHomeSlots(page) {
  await page.getByTestId('slot-matchGrid').waitFor()
  return page.evaluate(async () => {
    await document.fonts.ready
    const box = (id) => document.querySelector(`[data-testid="${id}"]`).getBoundingClientRect().toJSON()
    return { spot: box('slot-spotlight'), news: box('slot-news'), grid: box('slot-matchGrid') }
  })
}

test.describe('inicio (RF-32 a RF-36)', () => {
  test('a 1440 px: spotlight 2/3, noticias 1/3 a su derecha y cuadrícula debajo', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/')
    const { spot, news, grid } = await measureHomeSlots(page)
    expect(Math.abs(spot.y - news.y)).toBeLessThanOrEqual(1)
    expect(news.x).toBeGreaterThan(spot.x + spot.width - 1)
    expect(spot.width / news.width).toBeGreaterThan(1.9)
    expect(spot.width / news.width).toBeLessThan(2.2)
    expect(grid.y).toBeGreaterThanOrEqual(spot.y + spot.height)
    expect(grid.width).toBeGreaterThan(spot.width + news.width)
  })

  test('a 1023 px: una columna con spotlight, noticias y cuadrícula', async ({ page }) => {
    await page.setViewportSize({ width: 1023, height: 900 })
    await page.goto('/')
    const { spot, news, grid } = await measureHomeSlots(page)
    expect(news.y).toBeGreaterThanOrEqual(spot.y + spot.height)
    expect(grid.y).toBeGreaterThanOrEqual(news.y + news.height)
    expect(Math.round(spot.width)).toBe(Math.round(news.width))
  })
})

test.describe('sin scroll horizontal (RF-4)', () => {
  for (const lang of ['es', 'en']) {
    for (const width of WIDTHS) {
      test(`${lang} a ${width} px en todas las rutas`, async ({ page }) => {
        await setBrowserLanguages(page, [lang])
        await page.setViewportSize({ width, height: 800 })
        for (const path of [...SECTION_PATHS, '/no-existe']) {
          await page.goto(path)
          await expectNoHorizontalScroll(page)
        }
      })
    }
  }
})

test.describe('tema oscuro (RF-5)', () => {
  test('se mantiene oscuro con el sistema en modo claro', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'light' })
    await page.goto('/')
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor)
    expect(bg).toBe('rgb(11, 13, 18)')
  })
})
