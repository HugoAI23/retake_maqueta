import { expect, test } from '@playwright/test'
import { expectNoA11yViolations, mainNav, mockSeason } from './helpers.js'

// Spec 003 (T-082): acceso, bloqueo y cierre de sesión de /admin, con la API simulada en el navegador.
// La contraseña es ficticia: la real la crea Hugo con `retake set-admin-password`.
const SOURCES = [
  { source: 'bp', lastAttemptAt: '2026-12-05T19:00:00Z', lastSuccessAt: '2026-12-05T19:00:00Z', stopped: false,
    refreshable: true, reason: null, activeRequest: null },
  { source: 'wiki', lastAttemptAt: '2026-08-01T12:00:00Z', lastSuccessAt: '2026-08-01T12:00:00Z', stopped: false,
    refreshable: false, reason: 'x', activeRequest: null },
  { source: 'cdl', lastAttemptAt: null, lastSuccessAt: null, stopped: false, refreshable: false, reason: 'x', activeRequest: null },
]

async function fakeAdminApi(page, { loginStatus = 200 } = {}) {
  const state = { signedIn: false, headers: [] }
  await page.route('**/api/admin/**', async (route) => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    if (request.method() === 'POST') state.headers.push(request.headers()['x-retake-admin'])
    if (path.endsWith('/login')) {
      if (loginStatus === 200) state.signedIn = true
      return route.fulfill({ status: loginStatus, json: loginStatus === 200 ? { username: 'hugo' } : { detail: 'x' } })
    }
    if (path.endsWith('/logout')) {
      state.signedIn = false
      return route.fulfill({ status: 204, body: '' })
    }
    if (!state.signedIn) return route.fulfill({ status: 401, json: { detail: 'x' } })
    if (path.endsWith('/me')) return route.fulfill({ json: { username: 'hugo' } })
    if (path.endsWith('/sources')) return route.fulfill({ json: SOURCES })
    if (path.endsWith('/log')) return route.fulfill({ json: { page: 1, pageSize: 50, runs: [], incidents: [] } })
    if (path.endsWith('/summaries')) return route.fulfill({ json: [] })
    return route.fulfill({ status: 404, json: { detail: 'x' } })
  })
  return state
}

async function signIn(page, password = 'contraseña-ficticia') {
  await page.getByLabel('Usuario').fill('hugo')
  await page.getByLabel('Contraseña').fill(password)
  await page.getByRole('button', { name: 'Entrar' }).click()
}

test.describe('administración (RF-97 a RF-139)', () => {
  test.beforeEach(async ({ page }) => mockSeason(page))

  test('dentro del marco común y sin entrada en el menú (RF-97 a RF-99)', async ({ page }) => {
    await fakeAdminApi(page)
    await page.goto('/admin')
    await expect(page.getByRole('heading', { name: 'Acceso de administración' })).toBeVisible()
    await expect(mainNav(page).locator('a[href="/admin"]')).toHaveCount(0)
    await expect(mainNav(page).locator('[aria-current="page"]')).toHaveCount(0)
    await expect(page.getByRole('contentinfo')).toBeVisible()
    await expectNoA11yViolations(page)
  })

  test('credenciales incorrectas: un único mensaje (RF-126)', async ({ page }) => {
    await fakeAdminApi(page, { loginStatus: 401 })
    await page.goto('/admin')
    await signIn(page, 'mala')
    await expect(page.getByRole('alert')).toHaveText('Usuario o contraseña incorrectos.')
  })

  test('origen bloqueado (RF-127 a RF-129)', async ({ page }) => {
    await fakeAdminApi(page, { loginStatus: 429 })
    await page.goto('/admin')
    await signIn(page)
    await expect(page.getByRole('alert')).toContainText('15 minutos')
  })

  test('acceso, paneles y cierre de sesión (RF-125, RF-138; D-11)', async ({ page }) => {
    const api = await fakeAdminApi(page)
    await page.goto('/admin')
    await signIn(page)
    await expect(page.getByRole('heading', { name: 'Estado de las fuentes' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Actualizar BreakingPoint.gg' })).toBeEnabled()
    await expectNoA11yViolations(page)
    await page.getByRole('button', { name: 'Cerrar sesión' }).click()
    await expect(page.getByRole('heading', { name: 'Acceso de administración' })).toBeVisible()
    expect(api.headers.every((value) => value === '1')).toBe(true)
  })
})
