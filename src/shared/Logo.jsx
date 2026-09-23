import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router'

/**
 * Ruta de la imagen del logo. Es `null` mientras Hugo no aporte el archivo
 * (dependencia externa de tasks.md); en ese caso se muestra el texto, igual
 * que cuando la imagen falla (RF-13).
 * @type {string | null}
 */
export const LOGO_SRC = null

/**
 * Logo de Retake enlazado a Inicio (RF-11, RF-12). Si la imagen no se puede
 * cargar, muestra el texto "Retake" sin perder el enlace (RF-13).
 *
 * @param {{ src?: string | null }} props `src` permite probar el fallo de la imagen.
 */
export function Logo({ src = LOGO_SRC }) {
  const { t } = useTranslation()
  const [failed, setFailed] = useState(false)
  const showImage = Boolean(src) && !failed

  return (
    <Link
      to="/"
      aria-label={t('logo.homeLink')}
      className="inline-flex min-h-11 items-center rounded-md px-1 text-xl font-black tracking-tight text-text hover:text-accent active:opacity-80"
    >
      {showImage ? (
        <img src={src} alt="" className="h-8 w-auto" onError={() => setFailed(true)} />
      ) : (
        <span>Retake</span>
      )}
    </Link>
  )
}
