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
  },
}
