/**
 * Escenarios de la página de demostración (plan §3.5, RF-91 a RF-93).
 * Solo se usan en desarrollo.
 *
 * @typedef {'ok' | 'fail' | 'hang' | 'late'} DemoScenario
 */

/** @type {DemoScenario[]} */
export const DEMO_SCENARIOS = ['ok', 'fail', 'hang', 'late']

/** Tiempos de cada escenario, en milisegundos. */
export const DEMO_TIMINGS = { ok: 1000, fail: 1000, late: 20000 }

/**
 * Contenido de prueba. Incluye nombres propios de la liga para comprobar que
 * no se traducen al cambiar de idioma (RF-72).
 */
export const DEMO_DATA = Object.freeze({
  home: 'FaZe VGS',
  away: 'OpTic Texas',
  mode: 'Hardpoint',
  map: 'Vault',
  event: 'Major 2 Qualifiers',
  startsAt: new Date(2026, 8, 21, 18, 30),
})

/**
 * Crea una operación de carga falsa para un escenario.
 *
 * - `ok`: los datos llegan en 1 s.
 * - `fail`: la carga falla en 1 s (RF-92).
 * - `hang`: la carga no termina nunca, así que el error sale a los 15 s (RF-91).
 * - `late`: los datos llegan a los 20 s, después del error de los 15 s (RF-91, RF-93).
 *
 * @param {DemoScenario} scenario
 * @returns {() => Promise<typeof DEMO_DATA>}
 */
export function createDemoLoad(scenario) {
  return () =>
    new Promise((resolve, reject) => {
      if (scenario === 'ok') setTimeout(() => resolve(DEMO_DATA), DEMO_TIMINGS.ok)
      if (scenario === 'fail') setTimeout(() => reject(new Error('Fallo simulado')), DEMO_TIMINGS.fail)
      if (scenario === 'late') setTimeout(() => resolve(DEMO_DATA), DEMO_TIMINGS.late)
      // 'hang': la promesa no se resuelve nunca.
    })
}
