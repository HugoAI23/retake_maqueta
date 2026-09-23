/**
 * Textos de la interfaz en español (RF-63, RF-70).
 * Los nombres propios de la liga (franquicias, gamertags, eventos, mapas y
 * modos) NO se incluyen aquí: se muestran tal como llegan en los datos (RF-72).
 */
export default {
  app: {
    name: 'Retake',
    skipToContent: 'Saltar al contenido',
  },
  sections: {
    home: 'Inicio',
    matches: 'Partidos',
    teams: 'Equipos',
    players: 'Jugadores',
    tournaments: 'Torneos',
    standings: 'Posiciones',
    news: 'Noticias',
    mlModels: 'Modelos de ML',
  },
  blocks: {
    ticker: 'Cinta de marcadores',
    spotlight: 'Spotlight',
    news: 'Noticias',
    matchGrid: 'Próximos partidos',
  },
  nav: {
    mainLabel: 'Navegación principal',
    panelLabel: 'Menú de secciones',
    openMenu: 'Abrir menú',
    closeMenu: 'Cerrar menú',
    mlBadge: 'IA',
  },
  logo: {
    homeLink: 'Retake, ir a Inicio',
  },
  language: {
    label: 'Idioma',
  },
  status: {
    comingSoon: 'Próximamente',
    loading: 'Cargando…',
    loadError: 'No se pudo cargar este contenido.',
    retry: 'Reintentar',
    retryBlock: 'Reintentar: {{block}}',
    offline: 'Sin conexión. Mostramos lo que ya estaba cargado.',
  },
  home: {
    heading: 'Retake: estadísticas y predicciones de la Call of Duty League',
  },
  notFound: {
    title: 'Página no encontrada',
    message: 'La dirección que buscas no existe en Retake.',
    backHome: 'Volver a Inicio',
  },
  footer: {
    disclaimer:
      'Proyecto escolar sin afiliación oficial con la Call of Duty League.',
    season: 'Temporada {{year}}',
  },
  league: {
    matchStatus: {
      scheduled: 'programado',
      live: 'en vivo',
      finished: 'finalizado',
    },
    notAvailable: 'No disponible',
    noRole: 'Sin rol',
    statsPending: 'Estadísticas pendientes',
    phase: {
      week: 'semana',
      group: 'grupo',
      winnersBracket: 'winners bracket',
      losersBracket: 'losers bracket',
      final: 'final',
    },
  },
}
