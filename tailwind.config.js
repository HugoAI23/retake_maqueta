import { colors } from './src/config/designTokens.js'

// Tailwind lee los colores del módulo compartido de variables de diseño,
// así la paleta y la prueba de contraste nunca se desincronizan (T-004).
export default {
  theme: {
    extend: {
      colors,
    },
  },
}
