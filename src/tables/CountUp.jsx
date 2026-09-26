import { useRowProgress } from './useTableMotion.js'

/**
 * Valor a una fracción de su camino desde 0: número o balance ({ won, lost }).
 * @param {number | Record<string, number>} value
 * @param {number} progress 0–1
 */
function scale(value, progress) {
  if (typeof value === 'number') return Math.round(value * progress)
  return Object.fromEntries(Object.entries(value).map(([key, v]) => [key, typeof v === 'number' ? Math.round(v * progress) : v]))
}

/**
 * Cifra que cuenta desde 0 en la entrada de la tabla (spec 004, RF-28, RF-50a).
 *
 * La cifra que cuenta es solo visual (`aria-hidden`); al lado, una copia oculta a la vista
 * lleva el valor final desde el primer momento para los lectores de pantalla (RF-34, D-10).
 *
 * @template V
 * @param {{ value: V, format: (value: V) => string }} props `value`: número o balance.
 */
export function CountUp({ value, format }) {
  const progress = useRowProgress()
  const shown = progress >= 1 || value === null || value === undefined ? value : scale(value, progress)
  return (
    <>
      <span aria-hidden="true">{format(shown)}</span>
      <span className="sr-only">{format(value)}</span>
    </>
  )
}
