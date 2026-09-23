/**
 * Variables de diseño del tema oscuro de Retake (spec 001, RF-5 y RF-74).
 *
 * Es la única fuente de los colores: la leen Tailwind (tailwind.config.js)
 * y la prueba de contraste (designTokens.test.js), que exige 4,5:1 en
 * cada pareja de texto y fondo declarada en `contrastPairs`.
 */
export const colors = {
  bg: '#0b0d12',
  surface: '#151922',
  raised: '#1f2531',
  border: '#2c3444',
  text: '#f2f4f8',
  muted: '#a9b2c3',
  accent: '#4fd1ff',
  ml: '#6d28d9',
  'on-ml': '#ffffff',
  focus: '#ffd166',
  danger: '#ff7b7b',
  // Fondo del escudo de un equipo sin logo ni color primario (spec 002, RF-118).
  // El texto encima es blanco o negro según el contraste (RF-127, RF-128).
  'team-neutral': '#3a4252',
}

/**
 * Parejas [texto, fondo] que aparecen en el marco común.
 * Cada una debe alcanzar un contraste mínimo de 4,5:1 (RF-74).
 * @type {Array<[keyof typeof colors, keyof typeof colors]>}
 */
export const contrastPairs = [
  ['text', 'bg'],
  ['text', 'surface'],
  ['text', 'raised'],
  ['text', 'border'],
  ['muted', 'bg'],
  ['muted', 'surface'],
  ['muted', 'raised'],
  ['accent', 'bg'],
  ['accent', 'surface'],
  ['on-ml', 'ml'],
  ['danger', 'surface'],
  ['danger', 'bg'],
  ['focus', 'bg'],
  ['bg', 'focus'],
]
