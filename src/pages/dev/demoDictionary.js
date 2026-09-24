/**
 * Textos de la página de demostración (solo desarrollo).
 *
 * Viven aquí y no en los diccionarios principales para que no lleguen al
 * paquete de producción (RF-95, plan D-13). BlockDemoPage los registra en
 * i18next al montarse.
 */
export const demoDictionary = {
  es: {
    title: 'Demostración de bloque',
    intro:
      'Página solo de desarrollo para verificar la carga, los errores y la conexión de los bloques (RF-89 a RF-93).',
    scenarioLabel: 'Escenario de carga',
    scenarios: {
      ok: 'Carga correcta (1 s)',
      fail: 'Fallo de carga (1 s)',
      hang: 'Carga que no termina (error a los 15 s)',
      late: 'Datos tardíos (llegan a los 20 s)',
    },
    restart: 'Reiniciar bloque',
    loadCount: 'Intentos de carga iniciados: {{count}}',
    blockName: 'Bloque de demostración',
    sampleHeading: 'Partido de ejemplo',
    sampleMode: 'Modo',
    sampleMap: 'Mapa',
    live: {
      heading: 'Bloque en vivo (spec 003)',
      intro:
        'Partidos en vivo de la API, actualizados solos. Con `uv run retake source-mode simulated` y `uv run retake sync` se ven cambiar (RF-79 a RF-96, RF-155 a RF-159).',
      blockName: 'Partidos en vivo',
      empty: 'No hay ningún partido en vivo.',
    },
  },
  en: {
    title: 'Block demo',
    intro: 'Development-only page to verify block loading, errors and connection (RF-89 to RF-93).',
    scenarioLabel: 'Loading scenario',
    scenarios: {
      ok: 'Successful load (1 s)',
      fail: 'Failed load (1 s)',
      hang: 'Load that never ends (error at 15 s)',
      late: 'Late data (arrives at 20 s)',
    },
    restart: 'Restart block',
    loadCount: 'Load attempts started: {{count}}',
    blockName: 'Demo block',
    sampleHeading: 'Sample match',
    sampleMode: 'Mode',
    sampleMap: 'Map',
    live: {
      heading: 'Live block (spec 003)',
      intro:
        'Live matches from the API, updating on their own. Run `uv run retake source-mode simulated` and `uv run retake sync` to see them change (RF-79 to RF-96, RF-155 to RF-159).',
      blockName: 'Live matches',
      empty: 'There are no live matches.',
    },
  },
}
