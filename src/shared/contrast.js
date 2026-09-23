/**
 * Contraste de color según las WCAG 2.2 (spec 002, plan D-13).
 *
 * Lo usan la prueba de la paleta de la 001 (RF-74) y el escudo de equipo de la 002
 * (RF-127, RF-128), para que la fórmula exista en un solo sitio.
 */

/**
 * @param {string | null | undefined} hex Color `#rgb` o `#rrggbb`.
 * @returns {[number, number, number] | null} Canales rojo, verde y azul (0–255), o `null` si no es válido.
 */
export function parseHexColor(hex) {
  if (typeof hex !== 'string' || !/^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(hex)) return null
  const digits = hex.length === 4 ? [...hex.slice(1)].map((d) => d + d).join('') : hex.slice(1)
  const n = parseInt(digits, 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

function channel(value) {
  const c = value / 255
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
}

/**
 * Luminancia relativa de un color válido (0 = negro, 1 = blanco).
 * @param {string} hex
 */
export function relativeLuminance(hex) {
  const [r, g, b] = parseHexColor(hex)
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
}

/**
 * Relación de contraste entre dos colores válidos (de 1:1 a 21:1).
 * @param {string} a
 * @param {string} b
 */
export function contrastRatio(a, b) {
  const [light, dark] = [relativeLuminance(a), relativeLuminance(b)].sort((x, y) => y - x)
  return (light + 0.05) / (dark + 0.05)
}
