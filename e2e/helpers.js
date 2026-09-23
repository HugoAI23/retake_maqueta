import AxeBuilder from '@axe-core/playwright'
import { expect } from '@playwright/test'

/** Direcciones de todas las secciones del menú. */
export const SECTION_PATHS = ['/', '/matches', '/teams', '/players', '/tournaments', '/standings', '/news', '/ml-models']

/** Anchos de ventana que exige el criterio de finalización 3 de la spec. */
export const WIDTHS = [320, 1023, 1024, 1440]

/** Fuerza la lista de idiomas preferidos del navegador antes de cargar la página. */
export async function setBrowserLanguages(page, languages) {
  await page.addInitScript((langs) => {
    Object.defineProperty(navigator, 'languages', { get: () => langs })
    Object.defineProperty(navigator, 'language', { get: () => langs[0] })
  }, languages)
}

/** Comprueba que la página no tiene desplazamiento horizontal (RF-4). */
export async function expectNoHorizontalScroll(page) {
  const { scrollWidth, clientWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }))
  expect(scrollWidth, 'sin scroll horizontal').toBeLessThanOrEqual(clientWidth)
}

/** Auditoría automática de accesibilidad: WCAG 2.0, 2.1 y 2.2, niveles A y AA (RF-73). */
export async function expectNoA11yViolations(page) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22a', 'wcag22aa'])
    .analyze()
  const summary = results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)
  expect(summary).toEqual([])
}

export function mainNav(page) {
  return page.locator('header').getByRole('navigation')
}

export function menuButton(page) {
  return page.getByRole('button', { name: /^(Abrir|Cerrar) menú$|^(Open|Close) menu$/ }).first()
}
