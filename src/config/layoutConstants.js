/**
 * Constantes del marco común (spec 001, plan §1.2).
 */

/** Ancho a partir del cual el menú va en una fila y el inicio en dos columnas (RF-7, RF-16, RF-33). Coincide con el punto `lg` de Tailwind. */
export const WIDE_BREAKPOINT_PX = 1024

/** Consulta de medios equivalente a WIDE_BREAKPOINT_PX. */
export const WIDE_MEDIA_QUERY = `(min-width: ${WIDE_BREAKPOINT_PX}px)`

/** Duración máxima de un intento de carga de un bloque antes de tratarlo como fallo (RF-42). */
export const BLOCK_LOAD_TIMEOUT_MS = 15000

/** Duración máxima de cualquier animación del marco común (RF-87). */
export const MAX_ANIMATION_MS = 300

/** Ancho mínimo garantizado sin desplazamiento horizontal (RF-4). */
export const MIN_SUPPORTED_WIDTH_PX = 320
