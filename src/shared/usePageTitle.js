import { useEffect } from 'react'

const APP_NAME = 'Retake'

/**
 * Título de la pestaña del navegador (RF-30, RF-31).
 *
 * Con nombre de página: "<página> · Retake". Sin nombre (Inicio): "Retake".
 * El nombre llega ya traducido, así que el título cambia con el idioma.
 *
 * @param {string | null} pageName
 */
export function usePageTitle(pageName) {
  useEffect(() => {
    document.title = pageName ? `${pageName} · ${APP_NAME}` : APP_NAME
  }, [pageName])
}
